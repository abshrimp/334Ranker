<?php
// エラーレポーティングを有効にする
error_reporting(E_ALL);
ini_set('display_errors', 1);

// データベース接続
$servername = "";
$username = "";
$password = "";
$dbname = "";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// POSTデータの受け取り
$data = json_decode(file_get_contents('php://input'), true);

if (is_array($data)) {
    // プリペアドステートメントを作成
    $stmt = $conn->prepare("
        INSERT INTO rank (userid, best, best_count, max_pt, count, f, s, t, rankin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
        best = VALUES(best),
        best_count = VALUES(best_count),
        max_pt = VALUES(max_pt),
        count = VALUES(count),
        f = VALUES(f),
        s = VALUES(s),
        t = VALUES(t),
        rankin = VALUES(rankin)
    ");

    if ($stmt === false) {
        die("Prepare failed: " . $conn->error);
    }

    // データの各行を処理
    foreach ($data as $row) {
        if (count($row) !== 9) {
            die("Invalid data format");
        }

        // データのバインド
        $stmt->bind_param("isisiisii", $row[0], $row[1], $row[2], $row[3], $row[4], $row[5], $row[6], $row[7], $row[8]);

        // SQLを実行
        if (!$stmt->execute()) {
            echo "Execute failed: " . $stmt->error;
            exit;
        }
    }

    echo "Records created or updated successfully";
    $stmt->close();
} else {
    echo "Invalid data format";
}

$conn->close();
?>