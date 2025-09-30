examples = [
    {
        "query": "How much fund has been released in Maharashtra?",
        "sql": """
SELECT i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total_released
FROM pmayg_fund_fact ff
JOIN pmayg_state s ON ff.state_id = s.state_id
JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
WHERE s.name='MAHARASHTRA' AND i.name='Released_Total'
GROUP BY i.name;
"""
    },
    {
        "query": "Which beneficiary category received the most funds in Pune district?",
        "sql": """
SELECT i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
FROM pmayg_fund_fact ff
JOIN pmayg_district d ON ff.district_id = d.district_id
JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
WHERE d.name='PUNE' AND i.type='beneficiary'
GROUP BY i.name
ORDER BY total DESC;
"""
    },
    {
        "query": "Which beneficiary category received the least funds in Pune district?",
        "sql": """
SELECT i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
FROM pmayg_fund_fact ff
JOIN pmayg_district d ON ff.district_id = d.district_id
JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
WHERE d.name='PUNE' AND i.type='beneficiary'
GROUP BY i.name
ORDER BY total ASC;
"""
    },
    {
        "query": "Which beneficiary category is most underrepresented in Khed block?",
        "sql": """
SELECT i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
FROM pmayg_fund_fact ff
JOIN pmayg_block b ON ff.block_id = b.block_id
JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
WHERE b.name='KHED' AND i.type='beneficiary'
GROUP BY i.name
ORDER BY total ASC;
"""
    },
    {
        "query": "Compare fund allocation across beneficiary categories in Khed block",
        "sql": """
SELECT i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
FROM pmayg_fund_fact ff
JOIN pmayg_block b ON ff.block_id = b.block_id
JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
WHERE b.name='KHED' AND i.type='beneficiary'
GROUP BY i.name
ORDER BY total DESC;
"""
    },
    {
        "query": "Which beneficiary received the most funds in BHOSE panchayat?",
        "sql": """
SELECT i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
FROM pmayg_fund_fact ff
JOIN pmayg_panchayat p ON ff.panchayat_id = p.panchayat_id
JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
WHERE p.name='BHOSE' AND i.type='beneficiary'
GROUP BY i.name
ORDER BY total DESC;
"""
    },
    {
        "query": "Compare fund allocation across blocks in Maharashtra",
        "sql": """
SELECT b.name AS block_name, i.name AS indicator, COALESCE(SUM(ff.amount),0) AS total
FROM pmayg_fund_fact ff
JOIN pmayg_block b ON ff.block_id = b.block_id
JOIN pmayg_district d ON b.district_id = d.district_id
JOIN pmayg_state s ON d.state_id = s.state_id
JOIN pmayg_indicator i ON ff.indicator_id = i.indicator_id
WHERE s.name='MAHARASHTRA' AND i.type='beneficiary'
GROUP BY b.name, i.name
ORDER BY b.name, i.name;
"""
    }
]
