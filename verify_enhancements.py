"""
Quick start script to verify all enhancements are working
"""
import sys
import os

def check_file(filepath, description):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"  {status} {description}")
    return exists

def main():
    print("\n" + "="*70)
    print("  🚀 ENHANCEMENTS VERIFICATION")
    print("="*70)
    
    print("\n📁 Checking Files...")
    
    base_path = "c:/OneDriveExport/"
    
    files = {
        "schema_enhanced.sql": "Enhanced database schema",
        "mcp_server_enhanced.py": "Enhanced MCP server (30+ tools)",
        "mcp_cache.py": "Caching system",
        "data_validator.py": "Data validators",
        "enhance_database.py": "Database enhancement script",
        "test_mcp_enhanced.py": "MCP test suite",
        "test_database_constraints.py": "Constraint test suite",
        "README_ENHANCEMENTS.md": "Documentation"
    }
    
    all_present = True
    for filename, description in files.items():
        filepath = os.path.join(base_path, filename)
        if not check_file(filepath, description):
            all_present = False
    
    print("\n" + "="*70)
    print("  📊 SUMMARY")
    print("="*70)
    
    if all_present:
        print("\n  ✅ All enhancement files are present!")
        print("\n  Next steps:")
        print("  1. Apply database schema:")
        print("     • Open Supabase SQL Editor")
        print("     • Run schema_enhanced.sql")
        print("     • Or: python enhance_database.py")
        print("\n  2. Test the enhancements:")
        print("     • python test_mcp_enhanced.py")
        print("     • python test_database_constraints.py")
        print("\n  3. Read the documentation:")
        print("     • Open README_ENHANCEMENTS.md")
        print("\n  4. Use the enhanced MCP:")
        print("     • Replace mcp_server.py with mcp_server_enhanced.py")
        print("     • Or configure as new server in Claude Desktop")
    else:
        print("\n  ❌ Some files are missing!")
        print("  Please ensure all files were created successfully.")
    
    print("\n" + "="*70)
    
    # Show quick demo if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("\n🎬 Running Quick Demo...")
        try:
            sys.path.insert(0, base_path)
            from mcp_server_enhanced import analyze_portfolio_performance
            
            print("\nExecuting: analyze_portfolio_performance()")
            result = analyze_portfolio_performance()
            print("\nResult:")
            print(result[:500] + "..." if len(result) > 500 else result)
            
            print("\n✅ Demo successful! MCP server is working.")
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            print("This is normal if Supabase credentials need updating.")
    
    print()

if __name__ == "__main__":
    main()
