from core.database import get_db_connection


def get_tests_repo():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    name,
                    test_id,
                    test_name,
                    is_active,
                    creation,
                    modified
                FROM `tabTest Master`
                WHERE is_active = 1
                ORDER BY test_id
            """)

            return cursor.fetchall()


def get_appointment_types_repo():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    name,
                    appoinment_id,
                    appoinmnet_type_name,
                    is_active,
                    creation,
                    modified
                FROM `tabAppoinment Type Master`
                WHERE is_active = 1
                ORDER BY appoinment_id
            """)

            return cursor.fetchall()