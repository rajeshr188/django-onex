-- Type: money_value

-- DROP TYPE IF EXISTS public.money_value;

CREATE TYPE public.money_value AS
(
	amount numeric(14,3),
	currency character varying(3)
);

ALTER TYPE public.money_value
    OWNER TO postgres;

