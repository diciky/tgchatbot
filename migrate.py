from sqlalchemy import create_engine, text
from models import Base, engine

def migrate_database():
    """执行数据库迁移"""
    try:
        with engine.connect() as conn:
            # 检查 users 表是否存在
            result = conn.execute(text("SELECT * FROM sqlite_master WHERE type='table' AND name='users'"))
            table_info = result.fetchone()
            
            if table_info:
                # 检查列是否存在
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result.fetchall()]
                
                # 添加缺失的列
                if 'first_name' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(255)"))
                    print("成功添加 first_name 列")
                
                if 'last_name' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(255)"))
                    print("成功添加 last_name 列")
                
                if 'is_admin' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                    print("成功添加 is_admin 列")
                
                if 'updated_at' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    print("成功添加 updated_at 列")
                
                if 'verification_code' not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN verification_code VARCHAR(6)"))
                    print("成功添加 verification_code 列")
            
            # 检查 groups 表是否存在
            result = conn.execute(text("SELECT * FROM sqlite_master WHERE type='table' AND name='groups'"))
            table_info = result.fetchone()
            
            if table_info:
                # 检查列是否存在
                result = conn.execute(text("PRAGMA table_info(groups)"))
                columns = [row[1] for row in result.fetchall()]
                
                # 添加缺失的列
                if 'type' not in columns:
                    conn.execute(text("ALTER TABLE groups ADD COLUMN type VARCHAR(50)"))
                    print("成功添加 type 列")
                
                if 'updated_at' not in columns:
                    conn.execute(text("ALTER TABLE groups ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                    print("成功添加 updated_at 列")
            
            # 检查 messages 表是否存在
            result = conn.execute(text("SELECT * FROM sqlite_master WHERE type='table' AND name='messages'"))
            table_info = result.fetchone()
            
            if table_info:
                # 检查列是否存在
                result = conn.execute(text("PRAGMA table_info(messages)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'chat_type' not in columns:
                    conn.execute(text("ALTER TABLE messages ADD COLUMN chat_type VARCHAR(50) DEFAULT 'text'"))
                    print("成功添加 chat_type 列")
            
            # 检查 user_groups 表是否存在
            result = conn.execute(text("SELECT * FROM sqlite_master WHERE type='table' AND name='user_groups'"))
            table_info = result.fetchone()
            
            if not table_info:
                conn.execute(text("""
                    CREATE TABLE user_groups (
                        user_id INTEGER NOT NULL,
                        group_id INTEGER NOT NULL,
                        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, group_id),
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (group_id) REFERENCES groups (id)
                    )
                """))
                print("成功创建 user_groups 表")
            
            # 更新管理员状态
            admin_ids = "615346634,615346635"  # 从 .env 文件读取
            if admin_ids:
                admin_ids = admin_ids.split(',')
                for admin_id in admin_ids:
                    conn.execute(text(f"""
                        UPDATE users 
                        SET is_admin = TRUE 
                        WHERE telegram_id = {admin_id}
                    """))
                print("成功更新管理员状态")
            
            conn.commit()
            print("数据库迁移完成")
    except Exception as e:
        print(f"数据库迁移失败: {e}")

if __name__ == "__main__":
    migrate_database() 