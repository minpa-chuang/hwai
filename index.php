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
body { font-family: Arial, sans-serif; }
.floor { margin-bottom: 20px; }
.status { display: inline-block; width: 12px; height: 12px; border-radius: 50%; }
.status.up { background: #0f0; }
.status.down { background: #f00; }
.status.unknown { background: #ccc; }
</style>
</head>
<body>
<h1>Network Device Status</h1>
<p>Last updated: <?php echo htmlspecialchars($timestamp); ?></p>
<?php foreach ($byFloor as $floor => $list): ?>
<div class="floor">
  <h2>Floor <?php echo htmlspecialchars($floor); ?></h2>
  <table border="1" cellpadding="5" cellspacing="0">
    <tr><th>IP</th><th>Location</th><th>Status</th></tr>
    <?php foreach ($list as $device): ?>
    <tr>
      <td><?php echo htmlspecialchars($device['ip']); ?></td>
      <td><?php echo htmlspecialchars($device['location']); ?></td>
      <td><span class="status <?php echo htmlspecialchars($device['status']); ?>"></span> <?php echo htmlspecialchars($device['status']); ?></td>
    </tr>
    <?php endforeach; ?>
  </table>
</div>
<?php endforeach; ?>
</body>
</html>
