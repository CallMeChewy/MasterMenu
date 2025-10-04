import sqlite3
from collections import defaultdict

DATABASE_PATH = 'llm_tester.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DATABASE_PATH)

def generate_average_response_time_report(conn):
    """Generates a report on the average response time per model."""
    print("--- Average Response Time per Model (excluding loading prompts) ---")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT model_name, AVG(response_time)
        FROM test_results
        WHERE is_loading_prompt = 0
        GROUP BY model_name
        ORDER BY AVG(response_time) ASC
    """)
    results = cursor.fetchall()
    if not results:
        print("No data to report.")
        return

    for row in results:
        print(f"- {row[0]}: {row[1]:.4f} seconds")
    print("\n")

def generate_model_loading_time_report(conn):
    """Generates a report on the model loading times."""
    print("--- Model Loading Time ---")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT model_name, AVG(response_time)
        FROM test_results
        WHERE is_loading_prompt = 1
        GROUP BY model_name
        ORDER BY AVG(response_time) ASC
    """)
    results = cursor.fetchall()
    if not results:
        print("No loading time data to report.")
        return

    for row in results:
        print(f"- {row[0]}: {row[1]:.4f} seconds")
    print("\n")

def generate_task_performance_report(conn):
    """Generates a report on model performance for each task."""
    print("--- Task Performance ---")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT task, model_name, AVG(response_time)
        FROM test_results
        WHERE is_loading_prompt = 0
        GROUP BY task, model_name
        ORDER BY task, AVG(response_time) ASC
    """)
    results = cursor.fetchall()
    if not results:
        print("No task performance data to report.")
        return

    tasks = defaultdict(list)
    for row in results:
        tasks[row[0]].append((row[1], row[2]))

    for task, performances in tasks.items():
        print(f"Task: {task}")
        for model, avg_time in performances:
            print(f"  - {model}: {avg_time:.4f} seconds")
        print("")
    print("\n")

if __name__ == "__main__":
    try:
        conn = get_db_connection()
        generate_average_response_time_report(conn)
        generate_model_loading_time_report(conn)
        generate_task_performance_report(conn)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
