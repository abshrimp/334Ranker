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
    $stmt = $conn->prepare("INSERT INTO rank334 (userid, date, result, source) VALUES (?, ?, ?, ?)");

    if ($stmt === false) {
        die("Prepare failed: " . $conn->error);
    }

    // データの各行を処理
    foreach ($data as $row) {
        if (count($row) !== 4) {
            die("Invalid data format");
        }

        // データのバインド
        $stmt->bind_param("isss", $row[0], $row[1], $row[2], $row[3]);

        // SQLを実行
        if (!$stmt->execute()) {
            echo "Execute failed: " . $stmt->error;
            exit;
        }
    }

    echo "Records created successfully";
    $stmt->close();
} else {
    echo "Invalid data format";
}

$conn->close();
?>