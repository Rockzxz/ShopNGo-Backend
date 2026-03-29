import pymysql
pymysql.install_as_MySQLdb()

# 1. Bypass the XAMPP MariaDB version error
from django.db.backends.mysql.base import DatabaseWrapper
DatabaseWrapper.check_database_version_supported = lambda self: None

# 2. Force Django to NOT use the 'RETURNING' keyword (which MariaDB 10.4 doesn't understand)
from django.db.backends.mysql.features import DatabaseFeatures
DatabaseFeatures.can_return_columns_from_insert = False
DatabaseFeatures.can_return_rows_from_bulk_insert = False