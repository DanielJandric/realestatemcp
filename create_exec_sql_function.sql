-- Create RPC function to execute raw SQL queries
-- This allows Claude to run sophisticated SQL queries via MCP

CREATE OR REPLACE FUNCTION exec_sql(sql text)
RETURNS SETOF json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY EXECUTE 'SELECT row_to_json(t) FROM (' || sql || ') t';
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'SQL Error: %', SQLERRM;
END;
$$;

-- Grant execute permission to authenticated and service_role
GRANT EXECUTE ON FUNCTION exec_sql(text) TO service_role;
GRANT EXECUTE ON FUNCTION exec_sql(text) TO authenticated;

COMMENT ON FUNCTION exec_sql IS 'Execute raw SQL SELECT queries and return results as JSON. Security: Only SELECT queries should be passed.';

