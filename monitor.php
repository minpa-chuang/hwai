<?php
// Network device monitor script
set_time_limit(0);

$deviceFile = __DIR__ . '/devices.json';
$resultFile = __DIR__ . '/results.json';

if (!function_exists('pcntl_fork')) {
    fwrite(STDERR, "pcntl extension is required\n");
    exit(1);
}

function pingDevice($ip) {
    $cmd = sprintf('ping -c 3 %s 2>&1', escapeshellarg($ip));
    exec($cmd, $output, $ret);
    return $ret === 0; // 0 means success
}

while (true) {
    $devices = json_decode(file_get_contents($deviceFile), true);
    $children = [];
    $tempDir = sys_get_temp_dir();

    foreach ($devices as $index => $device) {
        $pid = pcntl_fork();
        if ($pid == -1) {
            continue; // fork failed
        } elseif ($pid) {
            $children[$pid] = $index;
        } else {
            $status = pingDevice($device['ip']) ? 'up' : 'down';
            $tmp = "$tempDir/monitor_{$index}.json";
            file_put_contents($tmp, json_encode(['index' => $index, 'status' => $status]));
            exit(0);
        }
    }

    foreach ($children as $pid => $index) {
        pcntl_waitpid($pid, $status);
    }

    $results = [
        'timestamp' => date('c'),
        'devices' => []
    ];

    foreach ($devices as $index => $device) {
        $tmp = "$tempDir/monitor_{$index}.json";
        if (file_exists($tmp)) {
            $data = json_decode(file_get_contents($tmp), true);
            unlink($tmp);
            $device['status'] = $data['status'];
        } else {
            $device['status'] = 'unknown';
        }
        $results['devices'][] = $device;
    }

    file_put_contents($resultFile, json_encode($results, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    sleep(300); // wait 5 minutes
}
