"""Logistics schema

Revision ID: 002
Revises: 001
Create Date: 2024-01-15

물류 운영 테이블 생성 (15개):
- warehouses: 창고 정보
- warehouse_zones: 창고 구역
- product_categories: 제품 카테고리
- products: 제품 마스터
- inventory: 재고 현황
- inventory_transactions: 재고 입출고 이력
- customers: 고객 정보
- orders: 주문
- order_items: 주문 상세
- carriers: 운송사
- vehicles: 차량 정보
- shipments: 배송
- shipment_items: 배송 상세
- delivery_routes: 배송 경로
- route_stops: 경로별 정류장
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === warehouses 테이블 ===
    op.execute("""
        CREATE TABLE warehouses (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            address TEXT,
            city VARCHAR(50),
            region VARCHAR(50),
            postal_code VARCHAR(20),
            phone VARCHAR(20),
            manager_name VARCHAR(100),
            capacity_sqm DECIMAL(10, 2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_warehouses_code ON warehouses(code)")
    op.execute("CREATE INDEX idx_warehouses_is_active ON warehouses(is_active)")
    op.execute("COMMENT ON TABLE warehouses IS '창고 정보'")
    op.execute("COMMENT ON COLUMN warehouses.code IS '창고 코드'")
    op.execute("COMMENT ON COLUMN warehouses.capacity_sqm IS '창고 면적 (제곱미터)'")

    # === warehouse_zones 테이블 ===
    op.execute("""
        CREATE TABLE warehouse_zones (
            id SERIAL PRIMARY KEY,
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
            code VARCHAR(20) NOT NULL,
            name VARCHAR(100) NOT NULL,
            zone_type VARCHAR(50),
            capacity_units INTEGER,
            temperature_min DECIMAL(5, 2),
            temperature_max DECIMAL(5, 2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(warehouse_id, code)
        )
    """)
    op.execute("CREATE INDEX idx_warehouse_zones_warehouse_id ON warehouse_zones(warehouse_id)")
    op.execute("COMMENT ON TABLE warehouse_zones IS '창고 구역'")
    op.execute("COMMENT ON COLUMN warehouse_zones.zone_type IS '구역 유형 (일반, 냉장, 냉동, 위험물)'")
    op.execute("COMMENT ON COLUMN warehouse_zones.capacity_units IS '수용 가능 유닛 수'")

    # === product_categories 테이블 ===
    op.execute("""
        CREATE TABLE product_categories (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            parent_id INTEGER REFERENCES product_categories(id),
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_product_categories_parent_id ON product_categories(parent_id)")
    op.execute("COMMENT ON TABLE product_categories IS '제품 카테고리'")
    op.execute("COMMENT ON COLUMN product_categories.parent_id IS '상위 카테고리 ID'")

    # === products 테이블 ===
    op.execute("""
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            category_id INTEGER REFERENCES product_categories(id),
            description TEXT,
            unit VARCHAR(20) DEFAULT 'EA',
            weight_kg DECIMAL(10, 3),
            length_cm DECIMAL(10, 2),
            width_cm DECIMAL(10, 2),
            height_cm DECIMAL(10, 2),
            unit_price DECIMAL(15, 2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_products_sku ON products(sku)")
    op.execute("CREATE INDEX idx_products_category_id ON products(category_id)")
    op.execute("CREATE INDEX idx_products_is_active ON products(is_active)")
    op.execute("COMMENT ON TABLE products IS '제품 마스터'")
    op.execute("COMMENT ON COLUMN products.sku IS '재고관리단위 코드'")
    op.execute("COMMENT ON COLUMN products.unit IS '단위 (EA, BOX, PALLET 등)'")

    # === inventory 테이블 ===
    op.execute("""
        CREATE TABLE inventory (
            id SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id),
            warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
            zone_id INTEGER REFERENCES warehouse_zones(id),
            quantity INTEGER NOT NULL DEFAULT 0,
            reserved_quantity INTEGER DEFAULT 0,
            lot_number VARCHAR(50),
            expiry_date DATE,
            last_counted_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product_id, warehouse_id, zone_id, lot_number)
        )
    """)
    op.execute("CREATE INDEX idx_inventory_product_id ON inventory(product_id)")
    op.execute("CREATE INDEX idx_inventory_warehouse_id ON inventory(warehouse_id)")
    op.execute("CREATE INDEX idx_inventory_zone_id ON inventory(zone_id)")
    op.execute("COMMENT ON TABLE inventory IS '재고 현황'")
    op.execute("COMMENT ON COLUMN inventory.quantity IS '실제 재고 수량'")
    op.execute("COMMENT ON COLUMN inventory.reserved_quantity IS '예약된 수량'")
    op.execute("COMMENT ON COLUMN inventory.lot_number IS '로트 번호'")

    # === inventory_transactions 테이블 ===
    op.execute("""
        CREATE TABLE inventory_transactions (
            id SERIAL PRIMARY KEY,
            inventory_id INTEGER NOT NULL REFERENCES inventory(id),
            transaction_type VARCHAR(20) NOT NULL,
            quantity INTEGER NOT NULL,
            reference_type VARCHAR(50),
            reference_id INTEGER,
            notes TEXT,
            performed_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_inv_trans_inventory_id ON inventory_transactions(inventory_id)")
    op.execute("CREATE INDEX idx_inv_trans_type ON inventory_transactions(transaction_type)")
    op.execute("CREATE INDEX idx_inv_trans_created_at ON inventory_transactions(created_at)")
    op.execute("COMMENT ON TABLE inventory_transactions IS '재고 입출고 이력'")
    op.execute("COMMENT ON COLUMN inventory_transactions.transaction_type IS '거래 유형 (IN, OUT, ADJUST, TRANSFER)'")
    op.execute("COMMENT ON COLUMN inventory_transactions.reference_type IS '참조 문서 유형 (ORDER, SHIPMENT, ADJUSTMENT)'")

    # === customers 테이블 ===
    op.execute("""
        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            contact_name VARCHAR(100),
            email VARCHAR(255),
            phone VARCHAR(20),
            address TEXT,
            city VARCHAR(50),
            region VARCHAR(50),
            postal_code VARCHAR(20),
            customer_type VARCHAR(20) DEFAULT 'regular',
            credit_limit DECIMAL(15, 2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_customers_code ON customers(code)")
    op.execute("CREATE INDEX idx_customers_is_active ON customers(is_active)")
    op.execute("COMMENT ON TABLE customers IS '고객 정보'")
    op.execute("COMMENT ON COLUMN customers.customer_type IS '고객 유형 (regular, vip, wholesale)'")

    # === orders 테이블 ===
    op.execute("""
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(30) UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            total_amount DECIMAL(15, 2),
            shipping_address TEXT,
            shipping_city VARCHAR(50),
            shipping_region VARCHAR(50),
            shipping_postal_code VARCHAR(20),
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_orders_order_number ON orders(order_number)")
    op.execute("CREATE INDEX idx_orders_customer_id ON orders(customer_id)")
    op.execute("CREATE INDEX idx_orders_status ON orders(status)")
    op.execute("CREATE INDEX idx_orders_order_date ON orders(order_date)")
    op.execute("COMMENT ON TABLE orders IS '주문'")
    op.execute("COMMENT ON COLUMN orders.status IS '주문 상태 (pending, confirmed, processing, shipped, delivered, cancelled)'")

    # === order_items 테이블 ===
    op.execute("""
        CREATE TABLE order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(15, 2) NOT NULL,
            discount_percent DECIMAL(5, 2) DEFAULT 0,
            line_total DECIMAL(15, 2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_order_items_order_id ON order_items(order_id)")
    op.execute("CREATE INDEX idx_order_items_product_id ON order_items(product_id)")
    op.execute("COMMENT ON TABLE order_items IS '주문 상세'")

    # === carriers 테이블 ===
    op.execute("""
        CREATE TABLE carriers (
            id SERIAL PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            contact_name VARCHAR(100),
            phone VARCHAR(20),
            email VARCHAR(255),
            service_types TEXT[],
            rating DECIMAL(3, 2),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_carriers_code ON carriers(code)")
    op.execute("CREATE INDEX idx_carriers_is_active ON carriers(is_active)")
    op.execute("COMMENT ON TABLE carriers IS '운송사'")
    op.execute("COMMENT ON COLUMN carriers.service_types IS '서비스 유형 배열 (express, standard, same_day)'")

    # === vehicles 테이블 ===
    op.execute("""
        CREATE TABLE vehicles (
            id SERIAL PRIMARY KEY,
            carrier_id INTEGER REFERENCES carriers(id),
            plate_number VARCHAR(20) UNIQUE NOT NULL,
            vehicle_type VARCHAR(50) NOT NULL,
            capacity_kg DECIMAL(10, 2),
            capacity_cbm DECIMAL(10, 2),
            fuel_type VARCHAR(20),
            year INTEGER,
            status VARCHAR(20) DEFAULT 'available',
            last_maintenance DATE,
            next_maintenance DATE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_vehicles_carrier_id ON vehicles(carrier_id)")
    op.execute("CREATE INDEX idx_vehicles_status ON vehicles(status)")
    op.execute("COMMENT ON TABLE vehicles IS '차량 정보'")
    op.execute("COMMENT ON COLUMN vehicles.vehicle_type IS '차량 유형 (truck_small, truck_medium, truck_large, van)'")
    op.execute("COMMENT ON COLUMN vehicles.status IS '차량 상태 (available, in_use, maintenance, retired)'")

    # === shipments 테이블 ===
    op.execute("""
        CREATE TABLE shipments (
            id SERIAL PRIMARY KEY,
            shipment_number VARCHAR(30) UNIQUE NOT NULL,
            order_id INTEGER REFERENCES orders(id),
            carrier_id INTEGER REFERENCES carriers(id),
            vehicle_id INTEGER REFERENCES vehicles(id),
            driver_id INTEGER REFERENCES drivers(id),
            status VARCHAR(20) DEFAULT 'pending',
            origin_warehouse_id INTEGER REFERENCES warehouses(id),
            destination_address TEXT,
            destination_city VARCHAR(50),
            destination_region VARCHAR(50),
            destination_postal_code VARCHAR(20),
            estimated_delivery TIMESTAMP WITH TIME ZONE,
            actual_delivery TIMESTAMP WITH TIME ZONE,
            shipping_cost DECIMAL(15, 2),
            tracking_number VARCHAR(50),
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_shipments_shipment_number ON shipments(shipment_number)")
    op.execute("CREATE INDEX idx_shipments_order_id ON shipments(order_id)")
    op.execute("CREATE INDEX idx_shipments_status ON shipments(status)")
    op.execute("CREATE INDEX idx_shipments_driver_id ON shipments(driver_id)")
    op.execute("COMMENT ON TABLE shipments IS '배송'")
    op.execute("COMMENT ON COLUMN shipments.status IS '배송 상태 (pending, picked_up, in_transit, out_for_delivery, delivered, returned)'")

    # === shipment_items 테이블 ===
    op.execute("""
        CREATE TABLE shipment_items (
            id SERIAL PRIMARY KEY,
            shipment_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            picked_quantity INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_shipment_items_shipment_id ON shipment_items(shipment_id)")
    op.execute("CREATE INDEX idx_shipment_items_product_id ON shipment_items(product_id)")
    op.execute("COMMENT ON TABLE shipment_items IS '배송 상세'")
    op.execute("COMMENT ON COLUMN shipment_items.picked_quantity IS '피킹 완료 수량'")

    # === delivery_routes 테이블 ===
    op.execute("""
        CREATE TABLE delivery_routes (
            id SERIAL PRIMARY KEY,
            route_code VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(100),
            vehicle_id INTEGER REFERENCES vehicles(id),
            driver_id INTEGER REFERENCES drivers(id),
            route_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'planned',
            start_time TIMESTAMP WITH TIME ZONE,
            end_time TIMESTAMP WITH TIME ZONE,
            total_distance_km DECIMAL(10, 2),
            total_stops INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_delivery_routes_route_date ON delivery_routes(route_date)")
    op.execute("CREATE INDEX idx_delivery_routes_vehicle_id ON delivery_routes(vehicle_id)")
    op.execute("CREATE INDEX idx_delivery_routes_driver_id ON delivery_routes(driver_id)")
    op.execute("CREATE INDEX idx_delivery_routes_status ON delivery_routes(status)")
    op.execute("COMMENT ON TABLE delivery_routes IS '배송 경로'")
    op.execute("COMMENT ON COLUMN delivery_routes.status IS '경로 상태 (planned, in_progress, completed, cancelled)'")

    # === route_stops 테이블 ===
    op.execute("""
        CREATE TABLE route_stops (
            id SERIAL PRIMARY KEY,
            route_id INTEGER NOT NULL REFERENCES delivery_routes(id) ON DELETE CASCADE,
            shipment_id INTEGER REFERENCES shipments(id),
            stop_sequence INTEGER NOT NULL,
            address TEXT,
            city VARCHAR(50),
            postal_code VARCHAR(20),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            planned_arrival TIMESTAMP WITH TIME ZONE,
            actual_arrival TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_route_stops_route_id ON route_stops(route_id)")
    op.execute("CREATE INDEX idx_route_stops_shipment_id ON route_stops(shipment_id)")
    op.execute("COMMENT ON TABLE route_stops IS '경로별 정류장'")
    op.execute("COMMENT ON COLUMN route_stops.stop_sequence IS '정류 순서'")
    op.execute("COMMENT ON COLUMN route_stops.status IS '정류 상태 (pending, arrived, completed, skipped)'")

    # === 물류 테이블 권한 설정 ===
    # Admin, Manager, Viewer 모두 물류 테이블 접근 가능
    logistics_tables = [
        'warehouses', 'warehouse_zones', 'product_categories', 'products',
        'inventory', 'inventory_transactions', 'customers', 'orders',
        'order_items', 'carriers', 'vehicles', 'shipments', 'shipment_items',
        'delivery_routes', 'route_stops'
    ]

    for table in logistics_tables:
        op.execute(f"""
            INSERT INTO table_permissions (role_id, table_name, can_read, can_write)
            SELECT r.id, '{table}', TRUE, CASE WHEN r.name = 'viewer' THEN FALSE ELSE TRUE END
            FROM roles r
            WHERE r.name IN ('admin', 'manager', 'viewer');
        """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS route_stops CASCADE;")
    op.execute("DROP TABLE IF EXISTS delivery_routes CASCADE;")
    op.execute("DROP TABLE IF EXISTS shipment_items CASCADE;")
    op.execute("DROP TABLE IF EXISTS shipments CASCADE;")
    op.execute("DROP TABLE IF EXISTS vehicles CASCADE;")
    op.execute("DROP TABLE IF EXISTS carriers CASCADE;")
    op.execute("DROP TABLE IF EXISTS order_items CASCADE;")
    op.execute("DROP TABLE IF EXISTS orders CASCADE;")
    op.execute("DROP TABLE IF EXISTS customers CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory_transactions CASCADE;")
    op.execute("DROP TABLE IF EXISTS inventory CASCADE;")
    op.execute("DROP TABLE IF EXISTS products CASCADE;")
    op.execute("DROP TABLE IF EXISTS product_categories CASCADE;")
    op.execute("DROP TABLE IF EXISTS warehouse_zones CASCADE;")
    op.execute("DROP TABLE IF EXISTS warehouses CASCADE;")

    # 물류 테이블 권한 삭제
    logistics_tables = [
        'warehouses', 'warehouse_zones', 'product_categories', 'products',
        'inventory', 'inventory_transactions', 'customers', 'orders',
        'order_items', 'carriers', 'vehicles', 'shipments', 'shipment_items',
        'delivery_routes', 'route_stops'
    ]
    for table in logistics_tables:
        op.execute(f"DELETE FROM table_permissions WHERE table_name = '{table}';")
