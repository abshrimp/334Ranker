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

// テーブルの全データを取得するSQLクエリ
$sql = "SELECT * FROM rank";
$result = $conn->query($sql);

$data = array();

if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        $data[] = $row;
    }
} else {
    echo "No results found";
}

$conn->close();

// JSON形式で返す
header('Content-Type: application/json');
echo json_encode($data);
?>