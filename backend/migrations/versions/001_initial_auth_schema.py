"""Initial authentication schema

Revision ID: 001
Revises: None
Create Date: 2024-01-15

인증 및 권한 관리를 위한 테이블 생성:
- users: 사용자 정보
- roles: 역할 (admin, manager, viewer)
- user_roles: 사용자-역할 매핑
- table_permissions: 테이블별 역할 권한
- drivers: 기사 개인정보 (Admin Only)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === users 테이블 ===
    op.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_users_email ON users(email);
        CREATE INDEX idx_users_is_active ON users(is_active);

        COMMENT ON TABLE users IS '사용자 정보';
        COMMENT ON COLUMN users.email IS '이메일 (로그인 ID)';
        COMMENT ON COLUMN users.password_hash IS 'bcrypt 해시된 비밀번호';
        COMMENT ON COLUMN users.name IS '사용자 이름';
        COMMENT ON COLUMN users.is_active IS '활성 상태';
    """)

    # === roles 테이블 ===
    op.execute("""
        CREATE TABLE roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        COMMENT ON TABLE roles IS '사용자 역할';
        COMMENT ON COLUMN roles.name IS '역할명 (admin, manager, viewer)';
        COMMENT ON COLUMN roles.description IS '역할 설명';

        -- 기본 역할 생성
        INSERT INTO roles (name, description) VALUES
            ('admin', '시스템 관리자 - 모든 테이블 접근 가능'),
            ('manager', '매니저 - 물류 운영 테이블 접근 가능'),
            ('viewer', '조회자 - 물류 운영 테이블 읽기 전용');
    """)

    # === user_roles 테이블 ===
    op.execute("""
        CREATE TABLE user_roles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, role_id)
        );

        CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
        CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

        COMMENT ON TABLE user_roles IS '사용자-역할 매핑';
    """)

    # === table_permissions 테이블 ===
    op.execute("""
        CREATE TABLE table_permissions (
            id SERIAL PRIMARY KEY,
            role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            table_name VARCHAR(100) NOT NULL,
            can_read BOOLEAN DEFAULT FALSE,
            can_write BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(role_id, table_name)
        );

        CREATE INDEX idx_table_permissions_role_id ON table_permissions(role_id);
        CREATE INDEX idx_table_permissions_table_name ON table_permissions(table_name);

        COMMENT ON TABLE table_permissions IS '테이블별 역할 권한';
        COMMENT ON COLUMN table_permissions.can_read IS '읽기 권한';
        COMMENT ON COLUMN table_permissions.can_write IS '쓰기 권한';
    """)

    # === drivers 테이블 (Admin Only) ===
    op.execute("""
        CREATE TABLE drivers (
            id SERIAL PRIMARY KEY,
            employee_id VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            email VARCHAR(255),
            license_number VARCHAR(50),
            license_type VARCHAR(50),
            license_expiry DATE,
            hire_date DATE,
            status VARCHAR(20) DEFAULT 'active',
            address TEXT,
            emergency_contact VARCHAR(100),
            emergency_phone VARCHAR(20),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX idx_drivers_employee_id ON drivers(employee_id);
        CREATE INDEX idx_drivers_status ON drivers(status);

        COMMENT ON TABLE drivers IS '기사 개인정보 (Admin Only)';
        COMMENT ON COLUMN drivers.employee_id IS '사원번호';
        COMMENT ON COLUMN drivers.license_number IS '운전면허 번호';
        COMMENT ON COLUMN drivers.license_type IS '면허 종류';
        COMMENT ON COLUMN drivers.status IS '상태 (active, inactive, on_leave)';
    """)

    # === 기본 권한 설정 ===
    # Admin: 모든 테이블 접근 가능 (인증 테이블 포함)
    # Manager/Viewer: 물류 운영 테이블만 접근 가능
    op.execute("""
        -- Admin 권한: 인증 테이블
        INSERT INTO table_permissions (role_id, table_name, can_read, can_write)
        SELECT r.id, t.table_name, TRUE, TRUE
        FROM roles r
        CROSS JOIN (
            VALUES ('users'), ('roles'), ('user_roles'), ('table_permissions'), ('drivers')
        ) AS t(table_name)
        WHERE r.name = 'admin';
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS table_permissions CASCADE;")
    op.execute("DROP TABLE IF EXISTS user_roles CASCADE;")
    op.execute("DROP TABLE IF EXISTS drivers CASCADE;")
    op.execute("DROP TABLE IF EXISTS roles CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
