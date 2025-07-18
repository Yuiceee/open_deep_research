<script lang="ts">
  import { onMount } from "svelte";
  import ProteinWorkflowViewer from "./lib/ProteinWorkflowViewer.svelte";
  import ControlPanel from "./lib/ControlPanel.svelte";
  import StatusPanel from "./lib/StatusPanel.svelte";

  let isConnected = $state(false);
  let currentStep = $state("input_analysis");
  let progress = $state(0);

  onMount(() => {
    console.log("App mounted");
  });
</script>

<main class="app">
  <header class="app-header">
    <h1>🧬 蛋白质设计工作流</h1>
    <div class="connection-status" class:connected={isConnected}>
      {isConnected ? "🟢 已连接" : "🔴 未连接"}
    </div>
  </header>

  <div class="app-content">
    <div class="left-panel">
      <ControlPanel />
      <StatusPanel {currentStep} {progress} />
    </div>

    <div class="main-panel">
      <ProteinWorkflowViewer />
    </div>
  </div>
</main>

<style>
  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    background: #f5f5f5;
  }

  .app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    border-bottom: 1px solid #e0e0e0;
  }

  .app-header h1 {
    margin: 0;
    color: #333;
    font-size: 1.5rem;
  }

  .connection-status {
    padding: 0.5rem 1rem;
    border-radius: 20px;
    background: #ffebee;
    color: #c62828;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .connection-status.connected {
    background: #e8f5e8;
    color: #2e7d32;
  }

  .app-content {
    display: flex;
    flex: 1;
    overflow: hidden;
  }

  .left-panel {
    width: 350px;
    background: white;
    border-right: 1px solid #e0e0e0;
    display: flex;
    flex-direction: column;
  }

  .main-panel {
    flex: 1;
    background: #fafafa;
    position: relative;
  }
</style>
