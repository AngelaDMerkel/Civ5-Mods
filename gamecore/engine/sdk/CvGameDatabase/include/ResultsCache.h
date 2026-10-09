// $Header
//------------------------------------------------------------------------------
#pragma once 

#include <unordered_map>

namespace Database{

class ResultsCache
{

public:
	CvGameDatabaseAPI ResultsCache(Connection& db);
	CvGameDatabaseAPI ~ResultsCache();

	//! Clear stored results
	CvGameDatabaseAPI void Clear();
	CvGameDatabaseAPI void Clear(const std::string& strKey);

	//! Retrieves the associated connection object.
	CvGameDatabaseAPI Database::Connection& Connection();

	//! Retrieves a cached result given an arbitrary string key
	CvGameDatabaseAPI Results* Get(const std::string& strKey);

	//! Prepares a cached result given an arbitrary string key
	CvGameDatabaseAPI Results* Prepare(const std::string& strKey, const char* szStmt, int lenStmt = -1);

	//! Returns the most recent database error message.
	CvGameDatabaseAPI const char* ErrorMessage() const;

private:
	ResultsCache(const ResultsCache&);	//Stub to prevent compiler generated function.
	ResultsCache& operator=(const ResultsCache&);	//Stub to prevent compiler generated function.

	Database::Connection& m_db;

	#if defined(__APPLE__)
	Database::LegacyTR1UnorderedMapStorage m_storedResults;
	#else
	typedef std::tr1::unordered_map<std::string, Results*> ResultsMap;
	ResultsMap m_storedResults;
	#endif
};

#if defined(__APPLE__)
static_assert(sizeof(ResultsCache) == 80,
	"Database::ResultsCache must match Aspyr's x86_64 ABI");
#endif


}	//namespace Database
