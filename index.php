<?php
$resultFile = __DIR__ . '/results.json';
$data = json_decode(file_get_contents($resultFile), true);
$timestamp = $data['timestamp'] ?? '';
$devices = $data['devices'] ?? [];
$byFloor = [];
foreach ($devices as $dev) {
    $byFloor[$dev['floor']][] = $dev;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Network Monitor</title>
<style>
body {
  font-family: Arial, sans-serif;
  background: #f4f4f4;
  margin: 0;
  padding: 20px;
}
h1 {
  text-align: center;
}
.floor {
  margin-bottom: 30px;
}
.floor-title {
  font-size: 1.2em;
  margin-bottom: 10px;
}
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}
.device-card {
  background: #fff;
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
}
.status {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}
.status.up { background: #4caf50; }
.status.down { background: #f44336; }
.status.unknown { background: #ccc; }
.device-info {
  display: flex;
  flex-direction: column;
}
</style>
</head>
<body>
<h1>Network Device Status</h1>
<p style="text-align:center;">Last updated: <?= htmlspecialchars($timestamp) ?></p>
<?php foreach ($byFloor as $floor => $list): ?>
<div class="floor">
  <div class="floor-title">Floor <?= htmlspecialchars($floor) ?></div>
  <div class="device-grid">
    <?php foreach ($list as $device): ?>
    <div class="device-card">
      <span class="status <?= htmlspecialchars($device['status']) ?>"></span>
      <div class="device-info">
        <div><?= htmlspecialchars($device['ip']) ?></div>
        <div><?= htmlspecialchars($device['location']) ?></div>
      </div>
    </div>
    <?php endforeach; ?>
  </div>
</div>
<?php endforeach; ?>
</body>
</html>
