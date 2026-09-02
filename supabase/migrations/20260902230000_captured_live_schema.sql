


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE TYPE "public"."message_channel" AS ENUM (
    'text',
    'voice'
);


ALTER TYPE "public"."message_channel" OWNER TO "postgres";


CREATE TYPE "public"."message_status" AS ENUM (
    'pending',
    'streaming',
    'complete',
    'failed'
);


ALTER TYPE "public"."message_status" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."assign_khata_number"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  IF NEW.khata_number IS NULL THEN
    SELECT COALESCE(MAX(khata_number), 0) + 1 INTO NEW.khata_number
    FROM public.customers WHERE shop_id = NEW.shop_id;
  END IF;
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."assign_khata_number"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."current_shop_id"() RETURNS "uuid"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    AS $$
  SELECT (auth.jwt() -> 'app_metadata' ->> 'shop_id')::uuid;
$$;


ALTER FUNCTION "public"."current_shop_id"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_auth_shop_id"() RETURNS "uuid"
    LANGUAGE "sql" STABLE SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
  SELECT shop_id 
  FROM public.profiles 
  WHERE id = auth.uid()
  LIMIT 1;
$$;


ALTER FUNCTION "public"."get_auth_shop_id"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_sold_item_stock"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  v_shop_id UUID;
BEGIN
  -- Fetch shop_id from parent sale record
  SELECT shop_id INTO v_shop_id
  FROM public.sales
  WHERE id = NEW.sale_id;

  -- 1. Deduct quantity from product stock
  UPDATE public.products
  SET stock = stock - NEW.quantity
  WHERE id = NEW.product_id;

  -- 2. Log entry in stock_movements table
  INSERT INTO public.stock_movements (id, shop_id, sale_id, product_id, quantity_change, created_at)
  VALUES (
    gen_random_uuid(),
    v_shop_id,
    NEW.sale_id,
    NEW.product_id,
    -NEW.quantity,
    NOW()
  );

  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."handle_sold_item_stock"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."handle_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."handle_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."is_admin"() RETURNS boolean
    LANGUAGE "sql" STABLE SECURITY DEFINER
    AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND role_name = 'admin'
  )
$$;


ALTER FUNCTION "public"."is_admin"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."process_sale"("p_customer_id" "uuid", "p_payment_type" "text", "p_items" "jsonb") RETURNS "uuid"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
DECLARE
  v_shop_id UUID;
  v_sale_id UUID;
  v_total_amount NUMERIC := 0;
  v_item JSONB;
  v_product_id UUID;
  v_quantity INT;
  v_unit_price NUMERIC;
BEGIN
  -- 1. Identify shop_id for the logged-in user
  v_shop_id := public.get_auth_shop_id();
  IF v_shop_id IS NULL THEN
    RAISE EXCEPTION 'Unauthorized: User is not linked to a valid shop.';
  END IF;

  -- 2. Calculate total sales amount from item payload
  FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
  LOOP
    v_quantity := (v_item->>'quantity')::INT;
    v_unit_price := (v_item->>'unit_price')::NUMERIC;
    v_total_amount := v_total_amount + (v_quantity * v_unit_price);
  END LOOP;

  -- 3. Create Master Sales Record (Ticket)
  INSERT INTO public.sales (
    id, shop_id, customer_id, payment_type, total_amount, created_by, created_at
  )
  VALUES (
    gen_random_uuid(), v_shop_id, p_customer_id, p_payment_type, v_total_amount, auth.uid(), NOW()
  )
  RETURNING id INTO v_sale_id;

  -- 4. Create Sold Items (Triggers auto-deduct stock and log stock_movements)
  FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
  LOOP
    v_product_id := (v_item->>'product_id')::UUID;
    v_quantity := (v_item->>'quantity')::INT;
    v_unit_price := (v_item->>'unit_price')::NUMERIC;

    INSERT INTO public.sold_items (
      id, sale_id, product_id, quantity, unit_price, created_at
    )
    VALUES (
      gen_random_uuid(), v_sale_id, v_product_id, v_quantity, v_unit_price, NOW()
    );
  END LOOP;

  -- 5. Handle Khata / Ledger entry if sale is on Credit
  IF LOWER(p_payment_type) IN ('credit', 'udhaar', 'khata') AND p_customer_id IS NOT NULL THEN
    INSERT INTO public.ledger_entries (
      id, shop_id, customer_id, sale_id, type, amount, created_by, created_at
    )
    VALUES (
      gen_random_uuid(), v_shop_id, p_customer_id, v_sale_id, 'debit', v_total_amount, auth.uid(), NOW()
    );
  END IF;

  RETURN v_sale_id;
END;
$$;


ALTER FUNCTION "public"."process_sale"("p_customer_id" "uuid", "p_payment_type" "text", "p_items" "jsonb") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."rls_auto_enable"() RETURNS "event_trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'pg_catalog'
    AS $$
DECLARE
  cmd record;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        EXECUTE format('alter table if exists %s enable row level security', cmd.object_identity);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$$;


ALTER FUNCTION "public"."rls_auto_enable"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."audit_log" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid",
    "shop_id" "uuid",
    "action_type" "text" NOT NULL,
    "details" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."audit_log" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "shop_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "created_by" "uuid"
);


ALTER TABLE "public"."conversations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."customers" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "shop_id" "uuid" NOT NULL,
    "khata_number" integer NOT NULL,
    "name" "text" NOT NULL,
    "cnic" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."customers" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."products" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "shop_id" "uuid" NOT NULL,
    "name" "text" NOT NULL,
    "sale_price" numeric(10,2) NOT NULL,
    "cost_price" numeric(10,2) NOT NULL,
    "stock" integer DEFAULT 0 NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "products_cost_price_check" CHECK (("cost_price" >= (0)::numeric)),
    CONSTRAINT "products_sale_price_check" CHECK (("sale_price" >= (0)::numeric))
);


ALTER TABLE "public"."products" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."sales" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "shop_id" "uuid" NOT NULL,
    "customer_id" "uuid",
    "payment_type" "text" NOT NULL,
    "total_amount" numeric(10,2) NOT NULL,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "sales_payment_type_check" CHECK (("payment_type" = ANY (ARRAY['cash'::"text", 'udhaar'::"text", 'split'::"text"]))),
    CONSTRAINT "sales_total_amount_check" CHECK (("total_amount" >= (0)::numeric))
);


ALTER TABLE "public"."sales" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."sold_items" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "sale_id" "uuid" NOT NULL,
    "product_id" "uuid" NOT NULL,
    "quantity" integer NOT NULL,
    "unit_price" numeric(10,2) NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "sold_items_quantity_check" CHECK (("quantity" > 0)),
    CONSTRAINT "sold_items_unit_price_check" CHECK (("unit_price" >= (0)::numeric))
);


ALTER TABLE "public"."sold_items" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."daily_sales_profit_view" AS
 SELECT "s"."shop_id",
    "date"("s"."created_at") AS "report_date",
    "sum"("s"."total_amount") AS "total_sales",
    ("sum"("s"."total_amount") - COALESCE("sum"((("si"."quantity")::numeric * "p"."cost_price")), (0)::numeric)) AS "total_profit"
   FROM (("public"."sales" "s"
     LEFT JOIN "public"."sold_items" "si" ON (("si"."sale_id" = "s"."id")))
     LEFT JOIN "public"."products" "p" ON (("p"."id" = "si"."product_id")))
  GROUP BY "s"."shop_id", ("date"("s"."created_at"));


ALTER VIEW "public"."daily_sales_profit_view" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."expense_categories" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."expense_categories" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."expenses" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "shop_id" "uuid" NOT NULL,
    "category_id" "uuid",
    "amount" numeric(10,2) NOT NULL,
    "note" "text",
    "expense_date" "date" DEFAULT CURRENT_DATE NOT NULL,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "expenses_amount_check" CHECK (("amount" > (0)::numeric))
);


ALTER TABLE "public"."expenses" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."ledger_entries" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "shop_id" "uuid" NOT NULL,
    "customer_id" "uuid" NOT NULL,
    "sale_id" "uuid",
    "type" "text" NOT NULL,
    "amount" numeric(10,2) NOT NULL,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "ledger_entries_amount_check" CHECK (("amount" > (0)::numeric)),
    CONSTRAINT "ledger_entries_type_check" CHECK (("type" = ANY (ARRAY['udhaar'::"text", 'payment'::"text"])))
);


ALTER TABLE "public"."ledger_entries" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."low_stock_view" AS
 SELECT "shop_id",
    "id" AS "product_id",
    "name",
    "stock"
   FROM "public"."products" "p"
  WHERE ("stock" <= 5);


ALTER VIEW "public"."low_stock_view" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."messages" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "conversation_id" "uuid" NOT NULL,
    "sender" "text" NOT NULL,
    "channel" "text" NOT NULL,
    "message" "text" NOT NULL,
    "transcription_confidence" double precision,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "status" "public"."message_status" DEFAULT 'complete'::"public"."message_status"
);


ALTER TABLE "public"."messages" OWNER TO "postgres";


CREATE OR REPLACE VIEW "public"."outstanding_udhaar_view" AS
 SELECT "c"."shop_id",
    "c"."id" AS "customer_id",
    "c"."khata_number",
    "c"."name" AS "customer_name",
    (COALESCE("sum"(
        CASE
            WHEN ("le"."type" = 'udhaar'::"text") THEN "le"."amount"
            ELSE (0)::numeric
        END), (0)::numeric) - COALESCE("sum"(
        CASE
            WHEN ("le"."type" = 'payment'::"text") THEN "le"."amount"
            ELSE (0)::numeric
        END), (0)::numeric)) AS "balance"
   FROM ("public"."customers" "c"
     LEFT JOIN "public"."ledger_entries" "le" ON (("le"."customer_id" = "c"."id")))
  GROUP BY "c"."shop_id", "c"."id", "c"."khata_number", "c"."name";


ALTER VIEW "public"."outstanding_udhaar_view" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."product_aliases" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "product_id" "uuid" NOT NULL,
    "alias" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."product_aliases" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."profiles" (
    "id" "uuid" NOT NULL,
    "shop_id" "uuid",
    "role_name" "text" DEFAULT 'shopkeeper'::"text",
    "email" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."profiles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."roles" (
    "name" "text" NOT NULL
);


ALTER TABLE "public"."roles" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."shops" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL,
    "address" "text",
    "location" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."shops" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."stock_movements" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "shop_id" "uuid" NOT NULL,
    "sale_id" "uuid",
    "product_id" "uuid" NOT NULL,
    "quantity_change" integer NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."stock_movements" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."tool_calls" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "message_id" "uuid" NOT NULL,
    "tool_name" "text" NOT NULL,
    "status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "params" "jsonb" DEFAULT '{}'::"jsonb" NOT NULL,
    "response" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "resolved_at" timestamp with time zone,
    CONSTRAINT "tool_calls_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'pending_approval'::"text", 'committed'::"text", 'rejected'::"text", 'undone'::"text", 'failed'::"text"])))
);


ALTER TABLE "public"."tool_calls" OWNER TO "postgres";


ALTER TABLE ONLY "public"."audit_log"
    ADD CONSTRAINT "audit_log_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "customers_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."expense_categories"
    ADD CONSTRAINT "expense_categories_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."expense_categories"
    ADD CONSTRAINT "expense_categories_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."expenses"
    ADD CONSTRAINT "expenses_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."ledger_entries"
    ADD CONSTRAINT "ledger_entries_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."product_aliases"
    ADD CONSTRAINT "product_aliases_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."products"
    ADD CONSTRAINT "products_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_pkey" PRIMARY KEY ("name");



ALTER TABLE ONLY "public"."sales"
    ADD CONSTRAINT "sales_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."shops"
    ADD CONSTRAINT "shops_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sold_items"
    ADD CONSTRAINT "sold_items_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."stock_movements"
    ADD CONSTRAINT "stock_movements_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."tool_calls"
    ADD CONSTRAINT "tool_calls_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "uq_customer_cnic_per_shop" UNIQUE ("shop_id", "cnic");



ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "uq_customer_khata_per_shop" UNIQUE ("shop_id", "khata_number");



ALTER TABLE ONLY "public"."product_aliases"
    ADD CONSTRAINT "uq_product_alias" UNIQUE ("product_id", "alias");



CREATE OR REPLACE TRIGGER "on_sold_item_created" AFTER INSERT ON "public"."sold_items" FOR EACH ROW EXECUTE FUNCTION "public"."handle_sold_item_stock"();



CREATE OR REPLACE TRIGGER "set_products_updated_at" BEFORE UPDATE ON "public"."products" FOR EACH ROW EXECUTE FUNCTION "public"."handle_updated_at"();



CREATE OR REPLACE TRIGGER "set_shops_updated_at" BEFORE UPDATE ON "public"."shops" FOR EACH ROW EXECUTE FUNCTION "public"."handle_updated_at"();



CREATE OR REPLACE TRIGGER "trg_assign_khata_number" BEFORE INSERT ON "public"."customers" FOR EACH ROW EXECUTE FUNCTION "public"."assign_khata_number"();



ALTER TABLE ONLY "public"."audit_log"
    ADD CONSTRAINT "audit_log_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."audit_log"
    ADD CONSTRAINT "audit_log_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."profiles"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."customers"
    ADD CONSTRAINT "customers_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."expenses"
    ADD CONSTRAINT "expenses_category_id_fkey" FOREIGN KEY ("category_id") REFERENCES "public"."expense_categories"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."expenses"
    ADD CONSTRAINT "expenses_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."profiles"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."expenses"
    ADD CONSTRAINT "expenses_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."ledger_entries"
    ADD CONSTRAINT "ledger_entries_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."profiles"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."ledger_entries"
    ADD CONSTRAINT "ledger_entries_customer_id_fkey" FOREIGN KEY ("customer_id") REFERENCES "public"."customers"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."ledger_entries"
    ADD CONSTRAINT "ledger_entries_sale_id_fkey" FOREIGN KEY ("sale_id") REFERENCES "public"."sales"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."ledger_entries"
    ADD CONSTRAINT "ledger_entries_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."product_aliases"
    ADD CONSTRAINT "product_aliases_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."products"
    ADD CONSTRAINT "products_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_role_name_fkey" FOREIGN KEY ("role_name") REFERENCES "public"."roles"("name") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."sales"
    ADD CONSTRAINT "sales_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "public"."profiles"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."sales"
    ADD CONSTRAINT "sales_customer_id_fkey" FOREIGN KEY ("customer_id") REFERENCES "public"."customers"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."sales"
    ADD CONSTRAINT "sales_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sold_items"
    ADD CONSTRAINT "sold_items_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE RESTRICT;



ALTER TABLE ONLY "public"."sold_items"
    ADD CONSTRAINT "sold_items_sale_id_fkey" FOREIGN KEY ("sale_id") REFERENCES "public"."sales"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."stock_movements"
    ADD CONSTRAINT "stock_movements_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."stock_movements"
    ADD CONSTRAINT "stock_movements_sale_id_fkey" FOREIGN KEY ("sale_id") REFERENCES "public"."sales"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."stock_movements"
    ADD CONSTRAINT "stock_movements_shop_id_fkey" FOREIGN KEY ("shop_id") REFERENCES "public"."shops"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."tool_calls"
    ADD CONSTRAINT "tool_calls_message_id_fkey" FOREIGN KEY ("message_id") REFERENCES "public"."messages"("id") ON DELETE CASCADE;



CREATE POLICY "Admins read all conversations, users read shop conversations" ON "public"."conversations" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" IN ( SELECT "profiles"."shop_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"())))));



CREATE POLICY "Admins read all messages, users read shop messages" ON "public"."messages" FOR SELECT USING (("public"."is_admin"() OR ("conversation_id" IN ( SELECT "conversations"."id"
   FROM "public"."conversations"
  WHERE ("conversations"."shop_id" IN ( SELECT "profiles"."shop_id"
           FROM "public"."profiles"
          WHERE ("profiles"."id" = "auth"."uid"())))))));



CREATE POLICY "Admins read all profiles, users read shop profiles" ON "public"."profiles" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" = "public"."current_shop_id"())));



CREATE POLICY "Admins read all shops, users read own shop" ON "public"."shops" FOR SELECT USING (("public"."is_admin"() OR ("id" IN ( SELECT "profiles"."shop_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"())))));



CREATE POLICY "Allow read access to roles" ON "public"."roles" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "Allow users to insert shops during registration" ON "public"."shops" FOR INSERT WITH CHECK (true);



CREATE POLICY "Authenticated users can insert shop" ON "public"."shops" FOR INSERT WITH CHECK (("auth"."role"() = 'authenticated'::"text"));



CREATE POLICY "Shopkeepers or Admins can access conversations" ON "public"."conversations" USING ((("shop_id" IN ( SELECT "profiles"."shop_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"()))) OR "public"."is_admin"()));



CREATE POLICY "Shopkeepers or Admins can access messages" ON "public"."messages" USING ((("conversation_id" IN ( SELECT "conversations"."id"
   FROM "public"."conversations"
  WHERE ("conversations"."shop_id" IN ( SELECT "profiles"."shop_id"
           FROM "public"."profiles"
          WHERE ("profiles"."id" = "auth"."uid"()))))) OR "public"."is_admin"()));



CREATE POLICY "Shopkeepers or Admins can view assigned shop" ON "public"."shops" FOR SELECT USING ((("id" IN ( SELECT "profiles"."shop_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"()))) OR "public"."is_admin"()));



CREATE POLICY "Users can access assigned shop" ON "public"."shops" TO "authenticated" USING (("id" = "public"."get_auth_shop_id"())) WITH CHECK (("id" = "public"."get_auth_shop_id"()));



CREATE POLICY "Users can access shop customers" ON "public"."customers" TO "authenticated" USING (("shop_id" = "public"."get_auth_shop_id"())) WITH CHECK (("shop_id" = "public"."get_auth_shop_id"()));



CREATE POLICY "Users can access shop ledger entries" ON "public"."ledger_entries" TO "authenticated" USING (("shop_id" = "public"."get_auth_shop_id"())) WITH CHECK (("shop_id" = "public"."get_auth_shop_id"()));



CREATE POLICY "Users can access shop product aliases" ON "public"."product_aliases" TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."products" "p"
  WHERE (("p"."id" = "product_aliases"."product_id") AND ("p"."shop_id" = "public"."get_auth_shop_id"()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."products" "p"
  WHERE (("p"."id" = "product_aliases"."product_id") AND ("p"."shop_id" = "public"."get_auth_shop_id"())))));



CREATE POLICY "Users can access shop products" ON "public"."products" TO "authenticated" USING (("shop_id" = "public"."get_auth_shop_id"())) WITH CHECK (("shop_id" = "public"."get_auth_shop_id"()));



CREATE POLICY "Users can access shop sales" ON "public"."sales" TO "authenticated" USING (("shop_id" = "public"."get_auth_shop_id"())) WITH CHECK (("shop_id" = "public"."get_auth_shop_id"()));



CREATE POLICY "Users can access shop stock movements" ON "public"."stock_movements" TO "authenticated" USING (("shop_id" = "public"."get_auth_shop_id"())) WITH CHECK (("shop_id" = "public"."get_auth_shop_id"()));



CREATE POLICY "Users can access sold items for their shop" ON "public"."sold_items" TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM "public"."sales" "s"
  WHERE (("s"."id" = "sold_items"."sale_id") AND ("s"."shop_id" = "public"."get_auth_shop_id"()))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."sales" "s"
  WHERE (("s"."id" = "sold_items"."sale_id") AND ("s"."shop_id" = "public"."get_auth_shop_id"())))));



CREATE POLICY "Users can insert own profile" ON "public"."profiles" FOR INSERT WITH CHECK (("auth"."uid"() = "id"));



CREATE POLICY "Users can manage own profile" ON "public"."profiles" TO "authenticated" USING (("id" = "auth"."uid"())) WITH CHECK (("id" = "auth"."uid"()));



CREATE POLICY "Users can update assigned shop" ON "public"."shops" FOR UPDATE USING (("id" IN ( SELECT "profiles"."shop_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"()))));



CREATE POLICY "Users can update own profile" ON "public"."profiles" FOR UPDATE USING (("auth"."uid"() = "id"));



CREATE POLICY "Users can view assigned shop" ON "public"."shops" FOR SELECT USING (("id" IN ( SELECT "profiles"."shop_id"
   FROM "public"."profiles"
  WHERE ("profiles"."id" = "auth"."uid"()))));



CREATE POLICY "Users insert conversations for own shop" ON "public"."conversations" FOR INSERT WITH CHECK (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "Users insert messages into own shop conversations" ON "public"."messages" FOR INSERT WITH CHECK (("conversation_id" IN ( SELECT "conversations"."id"
   FROM "public"."conversations"
  WHERE ("conversations"."shop_id" = "public"."current_shop_id"()))));



CREATE POLICY "Users or Admins can view profiles" ON "public"."profiles" FOR SELECT USING ((("auth"."uid"() = "id") OR "public"."is_admin"()));



CREATE POLICY "admin read audit log" ON "public"."audit_log" FOR SELECT USING ("public"."is_admin"());



ALTER TABLE "public"."audit_log" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "authenticated read expense categories" ON "public"."expense_categories" FOR SELECT USING (("auth"."role"() = 'authenticated'::"text"));



ALTER TABLE "public"."conversations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."customers" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."expense_categories" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."expenses" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."ledger_entries" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."messages" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."product_aliases" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."products" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."profiles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."roles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."sales" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "shop delete expenses" ON "public"."expenses" FOR DELETE USING (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop insert customers" ON "public"."customers" FOR INSERT WITH CHECK (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop insert expenses" ON "public"."expenses" FOR INSERT WITH CHECK (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop insert ledger entries" ON "public"."ledger_entries" FOR INSERT WITH CHECK (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop insert product aliases" ON "public"."product_aliases" FOR INSERT WITH CHECK (("product_id" IN ( SELECT "products"."id"
   FROM "public"."products"
  WHERE ("products"."shop_id" = "public"."current_shop_id"()))));



CREATE POLICY "shop insert products" ON "public"."products" FOR INSERT WITH CHECK (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop insert sales" ON "public"."sales" FOR INSERT WITH CHECK (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop insert sold items" ON "public"."sold_items" FOR INSERT WITH CHECK (("sale_id" IN ( SELECT "sales"."id"
   FROM "public"."sales"
  WHERE ("sales"."shop_id" = "public"."current_shop_id"()))));



CREATE POLICY "shop insert stock movements" ON "public"."stock_movements" FOR INSERT WITH CHECK (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop insert tool calls" ON "public"."tool_calls" FOR INSERT WITH CHECK (("message_id" IN ( SELECT "m"."id"
   FROM ("public"."messages" "m"
     JOIN "public"."conversations" "c" ON (("c"."id" = "m"."conversation_id")))
  WHERE ("c"."shop_id" = "public"."current_shop_id"()))));



CREATE POLICY "shop read customers" ON "public"."customers" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" = "public"."current_shop_id"())));



CREATE POLICY "shop read expenses" ON "public"."expenses" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" = "public"."current_shop_id"())));



CREATE POLICY "shop read ledger entries" ON "public"."ledger_entries" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" = "public"."current_shop_id"())));



CREATE POLICY "shop read product aliases" ON "public"."product_aliases" FOR SELECT USING (("public"."is_admin"() OR ("product_id" IN ( SELECT "products"."id"
   FROM "public"."products"
  WHERE ("products"."shop_id" = "public"."current_shop_id"())))));



CREATE POLICY "shop read products" ON "public"."products" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" = "public"."current_shop_id"())));



CREATE POLICY "shop read sales" ON "public"."sales" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" = "public"."current_shop_id"())));



CREATE POLICY "shop read sold items" ON "public"."sold_items" FOR SELECT USING (("public"."is_admin"() OR ("sale_id" IN ( SELECT "sales"."id"
   FROM "public"."sales"
  WHERE ("sales"."shop_id" = "public"."current_shop_id"())))));



CREATE POLICY "shop read stock movements" ON "public"."stock_movements" FOR SELECT USING (("public"."is_admin"() OR ("shop_id" = "public"."current_shop_id"())));



CREATE POLICY "shop read tool calls" ON "public"."tool_calls" FOR SELECT USING (("public"."is_admin"() OR ("message_id" IN ( SELECT "m"."id"
   FROM ("public"."messages" "m"
     JOIN "public"."conversations" "c" ON (("c"."id" = "m"."conversation_id")))
  WHERE ("c"."shop_id" = "public"."current_shop_id"())))));



CREATE POLICY "shop update products" ON "public"."products" FOR UPDATE USING (("shop_id" = "public"."current_shop_id"()));



CREATE POLICY "shop update tool calls" ON "public"."tool_calls" FOR UPDATE USING (("public"."is_admin"() OR ("message_id" IN ( SELECT "m"."id"
   FROM ("public"."messages" "m"
     JOIN "public"."conversations" "c" ON (("c"."id" = "m"."conversation_id")))
  WHERE ("c"."shop_id" = "public"."current_shop_id"())))));



ALTER TABLE "public"."shops" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."sold_items" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."stock_movements" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."tool_calls" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";






















































































































































GRANT ALL ON FUNCTION "public"."assign_khata_number"() TO "anon";
GRANT ALL ON FUNCTION "public"."assign_khata_number"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."assign_khata_number"() TO "service_role";



GRANT ALL ON FUNCTION "public"."current_shop_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."current_shop_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."current_shop_id"() TO "service_role";



GRANT ALL ON FUNCTION "public"."get_auth_shop_id"() TO "anon";
GRANT ALL ON FUNCTION "public"."get_auth_shop_id"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_auth_shop_id"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_sold_item_stock"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_sold_item_stock"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_sold_item_stock"() TO "service_role";



GRANT ALL ON FUNCTION "public"."handle_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."handle_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."handle_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."is_admin"() TO "anon";
GRANT ALL ON FUNCTION "public"."is_admin"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."is_admin"() TO "service_role";



GRANT ALL ON FUNCTION "public"."process_sale"("p_customer_id" "uuid", "p_payment_type" "text", "p_items" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."process_sale"("p_customer_id" "uuid", "p_payment_type" "text", "p_items" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."process_sale"("p_customer_id" "uuid", "p_payment_type" "text", "p_items" "jsonb") TO "service_role";


















GRANT ALL ON TABLE "public"."audit_log" TO "anon";
GRANT ALL ON TABLE "public"."audit_log" TO "authenticated";
GRANT ALL ON TABLE "public"."audit_log" TO "service_role";



GRANT ALL ON TABLE "public"."conversations" TO "anon";
GRANT ALL ON TABLE "public"."conversations" TO "authenticated";
GRANT ALL ON TABLE "public"."conversations" TO "service_role";



GRANT ALL ON TABLE "public"."customers" TO "anon";
GRANT ALL ON TABLE "public"."customers" TO "authenticated";
GRANT ALL ON TABLE "public"."customers" TO "service_role";



GRANT ALL ON TABLE "public"."products" TO "anon";
GRANT ALL ON TABLE "public"."products" TO "authenticated";
GRANT ALL ON TABLE "public"."products" TO "service_role";



GRANT ALL ON TABLE "public"."sales" TO "anon";
GRANT ALL ON TABLE "public"."sales" TO "authenticated";
GRANT ALL ON TABLE "public"."sales" TO "service_role";



GRANT ALL ON TABLE "public"."sold_items" TO "anon";
GRANT ALL ON TABLE "public"."sold_items" TO "authenticated";
GRANT ALL ON TABLE "public"."sold_items" TO "service_role";



GRANT ALL ON TABLE "public"."daily_sales_profit_view" TO "anon";
GRANT ALL ON TABLE "public"."daily_sales_profit_view" TO "authenticated";
GRANT ALL ON TABLE "public"."daily_sales_profit_view" TO "service_role";



GRANT ALL ON TABLE "public"."expense_categories" TO "anon";
GRANT ALL ON TABLE "public"."expense_categories" TO "authenticated";
GRANT ALL ON TABLE "public"."expense_categories" TO "service_role";



GRANT ALL ON TABLE "public"."expenses" TO "anon";
GRANT ALL ON TABLE "public"."expenses" TO "authenticated";
GRANT ALL ON TABLE "public"."expenses" TO "service_role";



GRANT ALL ON TABLE "public"."ledger_entries" TO "anon";
GRANT ALL ON TABLE "public"."ledger_entries" TO "authenticated";
GRANT ALL ON TABLE "public"."ledger_entries" TO "service_role";



GRANT ALL ON TABLE "public"."low_stock_view" TO "anon";
GRANT ALL ON TABLE "public"."low_stock_view" TO "authenticated";
GRANT ALL ON TABLE "public"."low_stock_view" TO "service_role";



GRANT ALL ON TABLE "public"."messages" TO "anon";
GRANT ALL ON TABLE "public"."messages" TO "authenticated";
GRANT ALL ON TABLE "public"."messages" TO "service_role";



GRANT ALL ON TABLE "public"."outstanding_udhaar_view" TO "anon";
GRANT ALL ON TABLE "public"."outstanding_udhaar_view" TO "authenticated";
GRANT ALL ON TABLE "public"."outstanding_udhaar_view" TO "service_role";



GRANT ALL ON TABLE "public"."product_aliases" TO "anon";
GRANT ALL ON TABLE "public"."product_aliases" TO "authenticated";
GRANT ALL ON TABLE "public"."product_aliases" TO "service_role";



GRANT ALL ON TABLE "public"."profiles" TO "anon";
GRANT ALL ON TABLE "public"."profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."profiles" TO "service_role";



GRANT ALL ON TABLE "public"."roles" TO "anon";
GRANT ALL ON TABLE "public"."roles" TO "authenticated";
GRANT ALL ON TABLE "public"."roles" TO "service_role";



GRANT ALL ON TABLE "public"."shops" TO "anon";
GRANT ALL ON TABLE "public"."shops" TO "authenticated";
GRANT ALL ON TABLE "public"."shops" TO "service_role";



GRANT ALL ON TABLE "public"."stock_movements" TO "anon";
GRANT ALL ON TABLE "public"."stock_movements" TO "authenticated";
GRANT ALL ON TABLE "public"."stock_movements" TO "service_role";



GRANT ALL ON TABLE "public"."tool_calls" TO "anon";
GRANT ALL ON TABLE "public"."tool_calls" TO "authenticated";
GRANT ALL ON TABLE "public"."tool_calls" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,USAGE ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,USAGE ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT SELECT,USAGE ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";



































