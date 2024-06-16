<?php

// Подключение к базе данных
$servername = "localhost";
$username = "username";
$password = "password";
$dbname = "Database.db";

$conn = new mysqli($servername, $username, $password, $dbname);

// Проверка подключения
if ($conn->connect_error) {
  die("Ошибка подключения: " . $conn->connect_error);
}

// Получение данных из формы
$name = $_POST["name"];
$email = $_POST["email"];
$message = $_POST["message"];

// Валидация данных
if (empty($name) || empty($email) || empty($message)) {
  echo "Заполните все поля!";
  exit;
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
  echo "Некорректный email!";
  exit;
}

// Подготовка SQL-запроса
$sql = "INSERT INTO feedback (name, email, message)
        VALUES ('$name', '$email', '$message')";

// Выполнение запроса
if ($conn->query($sql) === TRUE) {
  echo "Отзыв отправлен успешно!";
} else {
  echo "Ошибка: " . $conn->error;
}

// Закрытие подключения
$conn->close();

?>