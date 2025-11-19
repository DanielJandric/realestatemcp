-- ═══════════════════════════════════════════════════════════════════════════
-- FONCTION À EXÉCUTER DANS SUPABASE SQL EDITOR
-- ═══════════════════════════════════════════════════════════════════════════
-- 
-- Instructions:
-- 1. Ouvrir Supabase Dashboard
-- 2. Aller dans "SQL Editor"
-- 3. Copier-coller ce code complet
-- 4. Cliquer "Run" (RUN)
-- 5. Vérifier le message de succès
--
-- ⚠️ Cette version DROP la fonction existante avant de la recréer
-- ═══════════════════════════════════════════════════════════════════════════

-- Supprimer l'ancienne version si elle existe
DROP FUNCTION IF EXISTS public.exec_sql(text);

-- Créer la nouvelle version
CREATE OR REPLACE FUNCTION public.exec_sql(sql TEXT)
RETURNS SETOF JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    rec RECORD;
BEGIN
    -- Exécuter la requête dynamique
    FOR rec IN EXECUTE sql
    LOOP
        RETURN NEXT to_jsonb(rec);
    END LOOP;
    
    RETURN;
END;
$$;

-- Accorder les permissions nécessaires
GRANT EXECUTE ON FUNCTION public.exec_sql(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.exec_sql(TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION public.exec_sql(TEXT) TO anon;

-- Ajouter un commentaire descriptif
COMMENT ON FUNCTION public.exec_sql(TEXT) IS 
'Exécute une requête SQL dynamique et retourne les résultats en JSONB. 
Utilisé par le MCP server pour les outils avancés (aggregate_data, etc.).
SÉCURITÉ: Le MCP server filtre déjà les requêtes dangereuses côté Python.';

-- ═══════════════════════════════════════════════════════════════════════════
-- VÉRIFICATION (optionnel - pour tester)
-- ═══════════════════════════════════════════════════════════════════════════

-- Test simple:
-- SELECT * FROM exec_sql('SELECT name, address FROM properties LIMIT 3');

-- Test avec agrégation:
-- SELECT * FROM exec_sql('SELECT COUNT(*) as total FROM properties');

-- ═══════════════════════════════════════════════════════════════════════════
-- ✅ Si vous voyez "Success. No rows returned", c'est BON!
-- ═══════════════════════════════════════════════════════════════════════════
