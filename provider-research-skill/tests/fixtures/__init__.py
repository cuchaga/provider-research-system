"""Test fixtures and mock data."""

# Sample provider data
SAMPLE_PROVIDERS = [
    {
        "id": "provider-1",
        "npi": "1234567890",
        "legal_name": "Home Instead Senior Care - Boston",
        "address_city": "Boston",
        "address_state": "MA",
        "address_zip": "02101",
        "phone": "617-555-0100"
    },
    {
        "id": "provider-2",
        "npi": "2345678901",
        "legal_name": "Visiting Angels of Cambridge",
        "address_city": "Cambridge",
        "address_state": "MA",
        "address_zip": "02138",
        "phone": "617-555-0200"
    }
]

# Mock NPI response
MOCK_NPI_RESPONSE = {
    "results": [
        {
            "number": "1234567890",
            "name": "Home Instead Senior Care",
            "address": "123 Main St, Boston, MA 02101",
            "taxonomy": "Home Health Care"
        }
    ]
}

# Mock web scraping response
MOCK_WEB_CONTENT = """
<html>
<body>
    <div class="location">
        <h2>Home Instead - Boston</h2>
        <p>Address: 123 Main St, Boston, MA 02101</p>
        <p>Phone: (617) 555-0100</p>
    </div>
</body>
</html>
"""
