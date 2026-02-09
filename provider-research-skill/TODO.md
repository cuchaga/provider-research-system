# TODO: Add Top Home Healthcare Providers

## Objective
Add the top 10 largest home healthcare provider chains in the US to the database using the web researcher skill to gather data.

## Tasks

### Research & Planning
- [ ] Research top 10 US home healthcare chains

### Data Collection (Web Research Skill)
- [ ] Use web researcher skill for Home Instead data
- [ ] Use web researcher skill for Visiting Angels data
- [ ] Use web researcher skill for Right at Home data
- [ ] Use web researcher for remaining 7 top chains

### Validation & Database
- [ ] Validate all data with NPI registry
- [ ] Create batch insert script for providers
- [ ] Add all providers to database
- [ ] Verify database entries and run tests

---

## Target Providers

### Confirmed
1. Home Instead
2. Visiting Angels
3. Right at Home

### To Research
4-10. TBD (after initial research)

---

## Notes
- Use `ProviderWebResearcher` skill for data extraction
- Use `ProviderSemanticMatcher` for deduplication
- Validate against NPI registry before insertion
- Follow existing database schema in `provider_research/database/`

---

**Created:** February 9, 2026 (Evening)  
**Status:** Not Started  
**Priority:** Future Enhancement  
**Related Commit:** 2de6f7e
