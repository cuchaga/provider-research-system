#!/usr/bin/env python3
"""
Delete all entries from the providers database

⚠️  WARNING: This will permanently delete all provider data!
"""

import psycopg2
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'providers',
    'user': 'provider_admin',
    'password': 'provider123'
}

def main():
    print('\n' + '='*80)
    print('  ⚠️  DELETE ALL DATABASE ENTRIES')
    print('='*80)
    print()
    print('This will permanently delete:')
    print('  • All provider records')
    print('  • All historical data')
    print('  • All search history')
    print()
    
    # Connect and count records
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Count records in each table
        cur.execute('SELECT COUNT(*) FROM providers')
        provider_count = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM provider_history')
        history_count = cur.fetchone()[0]
        
        cur.execute('SELECT COUNT(*) FROM search_history')
        search_count = cur.fetchone()[0]
        
        print(f'Current database contents:')
        print(f'  Providers:        {provider_count:,} records')
        print(f'  History:          {history_count:,} records')
        print(f'  Search History:   {search_count:,} records')
        print()
        
        if provider_count == 0:
            print('✓ Database is already empty!')
            conn.close()
            return 0
        
        # Confirmation
        print('='*80)
        response = input('Are you sure you want to DELETE ALL DATA? Type "DELETE ALL" to confirm: ')
        
        if response != 'DELETE ALL':
            print('\n⏭  Deletion cancelled. No data was deleted.')
            conn.close()
            return 0
        
        # Second confirmation
        print()
        response2 = input('Final confirmation - type "YES" to proceed: ')
        
        if response2 != 'YES':
            print('\n⏭  Deletion cancelled. No data was deleted.')
            conn.close()
            return 0
        
        print('\n' + '='*80)
        print('Deleting all data...')
        print('='*80)
        
        # Delete in order (respecting foreign keys)
        print('\n1. Deleting search history...')
        cur.execute('DELETE FROM search_history')
        print(f'   ✓ Deleted {cur.rowcount} records')
        
        print('\n2. Deleting provider history...')
        cur.execute('DELETE FROM provider_history')
        print(f'   ✓ Deleted {cur.rowcount} records')
        
        print('\n3. Deleting all providers...')
        cur.execute('DELETE FROM providers')
        deleted_providers = cur.rowcount
        print(f'   ✓ Deleted {deleted_providers} records')
        
        # Commit the transaction
        conn.commit()
        
        print('\n' + '='*80)
        print('✓ ALL DATA DELETED SUCCESSFULLY')
        print('='*80)
        print(f'\nTotal records deleted: {deleted_providers + history_count + search_count:,}')
        print('\nDatabase is now empty.')
        print()
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f'\n❌ Error: {e}')
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print('\n\n⏭  Cancelled by user. No data was deleted.')
        sys.exit(130)
    except Exception as e:
        print(f'\n❌ Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
