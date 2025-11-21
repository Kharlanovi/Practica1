import sqlite3
import os

def init_database():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    add_initial_data(cursor)
    
    conn.commit()
    conn.close()
    print("База данных успешно инициализирована!")

def add_initial_data(cursor):

    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('admin', 'admin123', 'admin'))
    

    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('user', '111', 'user'))
    

    products = [
        ("Доска строганая 20x96x1000 мм хвоя сорт оптима ФГИС ЛК", 103.0, "assets/Доска1.webp"),
        ("Планкен 20x146x2000 мм хвоя сорт Оптима прямой с фаской угла", 354.0, "assets/Доска 2.webp"),
        ("Доска строганая 40x146x3000 мм хвоя сорт Оптима ФГИС ЛК", 887.0, "assets/Доска 3.webp"),
        ("Доска строганая 20x146x2000 мм хвоя сорт Оптима ФГИС ЛК", 354.0, "assets/Доска 4.webp"),
        ("Планкен Raggy wood хвойные деревья сорт АВ 2000x95x20мм 6шт", 4550.0, "assets/Доска 5.webp"),
        ("Доска Леспроф строганая 2400x95x20мм сосна сорт AB 6шт", 2400.0, "assets/Доска 6.webp"),
        ("Доска строганная Дом дерева 3000x90x20мм ель сорт AB 4шт", 1608.0, "assets/Доска 7.webp"),
        ("Доска строганная Дом дерева 3000x90x20мм ель сорт AB 4шт", 1815.0, "assets/Доска 8.webp"),
        ("Каска", 12345.0, "/assets/logo_banner.png")
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO products (name, price, image_url) VALUES (?, ?, ?)",
        products
    )

if __name__ == '__main__':
    init_database()