// Run Apps Script functions via clasp
function runSetup() {
  console.log("🎨 Running formatDashboard...");
  formatDashboard();
  
  console.log("⏰ Installing daily chart rebuild trigger...");
  installDailyChartRebuild();
  
  console.log("📊 Building all charts...");
  buildAllCharts();
  
  console.log("✅ Setup complete!");
}
 
