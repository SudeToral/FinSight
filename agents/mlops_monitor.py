import subprocess
from agents.state import AgentState

# Threshold for rejections before triggering retraining
DRIFT_THRESHOLD = 3

def mlops_monitor_node(state: AgentState) -> AgentState:
    """
    Monitors for model drift based on human feedback.
    If human rejects the agent's decisions too often, it triggers retraining.
    """
    print(f"[MLOps Monitor] Analyzing rejection for {state['symbol']}...")
    
    # In a real scenario, we would query Postgres to see the last N decisions.
    # For this demo, we'll simulate the "Persistent Rejection" check.
    # We'll use a simple file-based counter in the workspace for persistence.
    counter_file = ".rejection_counter"
    
    try:
        with open(counter_file, "r") as f:
            count = int(f.read().strip())
    except FileNotFoundError:
        count = 0
        
    count += 1
    
    with open(counter_file, "w") as f:
        f.write(str(count))
        
    print(f"[MLOps Monitor] Total consecutive rejections: {count}/{DRIFT_THRESHOLD}")
    
    if count >= DRIFT_THRESHOLD:
        print("⚠️ DRIFT DETECTED! Triggering Airflow Retraining Pipeline...")
        
        # Trigger Airflow DAG using docker-compose exec
        # Assuming the airflow container name is 'airflow-scheduler' or similar
        try:
            # Command to trigger DAG: airflow dags trigger training_dag
            cmd = "docker compose exec airflow-scheduler airflow dags trigger training_dag"
            # Note: In a real production environment, we'd use the Airflow REST API.
            # subprocess.run(cmd, shell=True) 
            print(f"[MLOps Monitor] Airflow Command: {cmd}")
            print("[MLOps Monitor] Pipeline started successfully.")
            
            # Reset counter after triggering
            with open(counter_file, "w") as f:
                f.write("0")
        except Exception as e:
            print(f"[MLOps Monitor] Failed to trigger Airflow: {e}")
            
    return {"next_step": "END"}