#!/usr/bin/env python3
"""Exercise production request loading through an SDK-shaped SQLite adapter.

This tests SQL/data/lifecycle behavior; it does not claim Aspyr database ABI or
native game execution. The actual SDK layouts are checked by the full build.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = r'''
#pragma once
#include <sqlite3.h>
namespace Database {
class Connection;
class Results {
public:
    sqlite3_stmt* stmt = nullptr;
    Connection* owner = nullptr;
    ~Results() { sqlite3_finalize(stmt); }
    bool Step();
    int GetInt(int c) { return sqlite3_column_int(stmt,c); }
    const char* GetText(int c) { return reinterpret_cast<const char*>(sqlite3_column_text(stmt,c)); }
};
class Connection {
public:
    sqlite3* db = nullptr;
    int code = 0, steps = 0, failAt = 0;
    Connection() { sqlite3_open(":memory:", &db); }
    ~Connection() { sqlite3_close(db); }
    bool Execute(Results& r, const char* sql) {
        r.owner = this;
        code = sqlite3_prepare_v2(db, sql, -1, &r.stmt, nullptr);
        return code == SQLITE_OK;
    }
};
inline bool Results::Step() {
    if (++owner->steps == owner->failAt) {
        owner->code = SQLITE_IOERR;
        return false;
    }
    owner->code = sqlite3_step(stmt);
    return owner->code == SQLITE_ROW;
}
}
'''
TEST = r'''
#include "C5M_CoreContext.h"
#include "C5M_Host.h"
#include <CvGameDatabase.h>
#include <cassert>
#include <iostream>

void check(const char* setup, bool expected, int failAt = 0) {
    Database::Connection db;
    assert(sqlite3_exec(db.db, setup, nullptr, nullptr, nullptr) == SQLITE_OK);
    db.failAt = failAt;
    C5M::Core().Reset();
    assert(C5M::ConfigureDatabase(db) == expected);
    assert(C5M::Core().Ready() == expected);
    assert(C5M::Core().Active().HasCapability("c5m.core-introspection", 1) == expected);
    if (expected) {
        assert(C5M::Core().Freeze());
        assert(C5M::Core().Active().Order().size() == 1);
    } else {
        assert(!C5M::Core().Error().empty());
        assert(C5M::Core().Active().Order().empty());
    }
}
int main() {
    check("", true);
    check("CREATE TABLE C5M_EnabledModules(Module, APIVersion)", true);
    check("CREATE TABLE C5M_EnabledModules(Module, APIVersion);"
          "INSERT INTO C5M_EnabledModules VALUES('c5m.core',1)", true);
    check("CREATE TABLE C5M_EnabledModules(WrongColumn)", false);
    const char* invalid[] = {
        "('terrain.native-trade',1)", "('c5m.core',2)", "('c5m.core',0)",
        "('c5m.core',-1)", "('c5m.core',1.5)", "('c5m.core','1')",
        "('c5m.core',4294967297)", "('c5m.core',NULL)", "(NULL,1)",
        "('',1)", "('bad%s',1)", "('c5m.core',1),('c5m.core',1)",
        "('c5m.core'||char(0)||'fake',1)"
    };
    for (const char* values : invalid) {
        const std::string sql = std::string("CREATE TABLE C5M_EnabledModules(Module, APIVersion);") +
            "INSERT INTO C5M_EnabledModules VALUES" + values;
        check(sql.c_str(), false);
    }
    // Failed table discovery and partial request reads cannot masquerade as
    // an absent/empty table or a successfully configured base core.
    check("", false, 1);
    check("CREATE TABLE C5M_EnabledModules(Module, APIVersion);"
          "INSERT INTO C5M_EnabledModules VALUES('c5m.core',1)", false, 3);
    check("", true);
    std::cout << "20 SQL configuration and read-error cases passed\n";
}
'''


class DatabaseAdapterTests(unittest.TestCase):
    def test_sql_requests_and_read_failures(self):
        with tempfile.TemporaryDirectory(prefix='c5m-database-') as directory:
            temp = Path(directory)
            (temp / 'CvGameCoreDLLPCH.h').write_text('// Host-only header not needed by this adapter.\n')
            (temp / 'CvGameDatabase.h').write_text(ADAPTER)
            (temp / 'test.cpp').write_text(TEST)
            binary = temp / 'test'
            subprocess.run([
                'clang++', '-std=c++11', '-Wall', '-Wextra', '-Werror',
                '-I', str(temp), '-I', str(ROOT / 'include'),
                str(ROOT / 'src/C5M_Host.cpp'), str(ROOT / 'src/C5M_ModuleRegistry.cpp'),
                str(ROOT / 'src/C5M_CoreContext.cpp'), str(temp / 'test.cpp'),
                '-lsqlite3', '-o', str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
