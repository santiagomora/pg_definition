#ifndef TEST_APP_BACKEND_FUNCTIONS
#define TEST_APP_BACKEND_FUNCTIONS
#include "test_app/database/queries.hpp"
#include "test_app/database/types.hpp"
#include "core_types/typing/types.hpp"


namespace ct = core_types;
namespace db = test_app_db;


namespace test_app
{
   std::optional<ct::text> get_author_name (const ct::int8&);
}


#endif
