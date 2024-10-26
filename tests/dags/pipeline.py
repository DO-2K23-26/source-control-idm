from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago

# Define the default arguments for the DAG
default_args = {
    'owner': 'your-username',
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Define the DAG (pipeline)
with DAG(
    'example_dag',                  # Name of the DAG
    default_args=default_args,       # Default arguments for tasks
    description='An example DAG',    # Description of the DAG
    schedule_interval='@daily',      # How often the DAG should run (daily in this case)
    catchup=False                    # Don't catch up on missed runs
) as dag:

    # Task 1: Print the date
    task_1 = BashOperator(
        task_id='print_date',
        bash_command='date'
    )

    # Task 2: Print "Hello World"
    task_2 = BashOperator(
        task_id='hello_world',
        bash_command='echo "Hello World"'
    )

    # Define task dependencies
    task_1 >> task_2

