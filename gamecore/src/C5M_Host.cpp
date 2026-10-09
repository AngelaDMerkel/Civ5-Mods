#include "CvGameCoreDLLPCH.h"
#include "../include/C5M_CoreContext.h"
#include "../include/C5M_Host.h"
#include <CvGameDatabase.h>

namespace C5M {
bool ConfigureDatabase(Database::Connection& db) {
    std::vector<Requirement> requests;
    Database::Results tables;
    // A count always produces one row. A failed Step must not be mistaken for
    // an absent table; Aspyr does not export the SDK's ErrorCode() method.
    if (!db.Execute(tables, "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='C5M_EnabledModules'") || !tables.Step())
        return Core().Reject("Cannot inspect the native module request table");
    if (tables.GetInt(0) != 0) {
        Database::Results rows;
        // Validate types/range in SQLite: ColumnType/GetInt64 are not exported
        // by this host. A final sentinel distinguishes completion from a
        // partial read failure without relying on localized error messages.
        if (!db.Execute(rows,
            "SELECT Module, APIVersion, CASE WHEN typeof(Module)='text' "
            "AND instr(Module,char(0))=0 AND typeof(APIVersion)='integer' "
            "AND APIVersion BETWEEN 1 AND 2147483647 THEN 1 ELSE 0 END AS C5MValid, "
            "0 AS C5MEnd FROM C5M_EnabledModules "
            "UNION ALL SELECT '',0,1,1 ORDER BY C5MEnd,Module"))
            return Core().Reject("C5M_EnabledModules requires Module and APIVersion columns");
        bool complete = false;
        while (rows.Step()) {
            if (rows.GetInt(3) == 1) { complete = true; break; }
            if (rows.GetInt(2) != 1)
                return Core().Reject("Invalid native module name or API version in C5M_EnabledModules");
            const char* name = rows.GetText(0);
            requests.push_back(Requirement(name ? name : "", static_cast<unsigned int>(rows.GetInt(1))));
        }
        if (!complete)
            return Core().Reject("Cannot finish reading C5M_EnabledModules");
    }
    return Core().Configure(requests);
}
}
