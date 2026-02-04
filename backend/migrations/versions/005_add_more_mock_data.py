"""Add more mock data

Revision ID: 005
Revises: 004
Create Date: 2024-02-04

"""
import random
from datetime import datetime, timedelta
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def get_random_date(days_back=30):
    """최근 30일 이내의 랜덤 날짜 반환"""
    end = datetime.now()
    start = end - timedelta(days=days_back)
    random_date = start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds()))
    )
    return random_date.strftime("%Y-%m-%d %H:%M:%S%z")

def get_random_phone():
    """랜덤 전화번호 생성"""
    return f"010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"

def upgrade() -> None:
    # 1. Warehouses (30개)
    warehouse_ids = []
    for i in range(30):
        code = f"WH-EXT-{i+1:03d}"
        op.execute(f"""
            INSERT INTO warehouses (code, name, address, city, region, postal_code, phone, manager_name, capacity_sqm, is_active)
            VALUES (
                '{code}',
                '확장 창고 {i+1}',
                '경기도 이천시 부발읍 가좌로 {100+i}',
                '이천',
                '경기',
                '{17300+i}',
                '{get_random_phone()}',
                '매니저{i+1}',
                {random.randint(1000, 5000)},
                true
            )
        """)
        # 방금 삽입한 ID 가져오기 (Postgres specific)
        # Alembic execute doesn't return ID easily without specialized handling,
        # so allow basic flow. For simplicity in mock data, we can assume auto-inc logic or fetch if needed,
        # but here we'll just insert child data based on logical assumption or independent selects if relationships were strict.
        # But to be safe for foreign keys, let's use subqueries or just insert loosely if safe.
        # Actually safer to select IDs.
    
    # FK 참조를 위해 ID 조회
    conn = op.get_bind()
    warehouses = conn.execute(sa.text("SELECT id, code FROM warehouses WHERE code LIKE 'WH-EXT-%'")).fetchall()
    warehouse_ids = [row[0] for row in warehouses]

    if not warehouse_ids: # Fallback if something went wrong, though execute above should work
         pass

    # 2. Warehouse Zones (각 창고당 2개씩 = 60개)
    zone_types = ['General', 'Cold', 'Frozen', 'Hazardous']
    for wh_id in warehouse_ids:
        for z in range(2):
            op.execute(f"""
                INSERT INTO warehouse_zones (warehouse_id, code, name, zone_type, capacity_units, temperature_min, temperature_max, is_active)
                VALUES (
                    {wh_id},
                    'Z-{wh_id}-{z+1}',
                    'Zone {z+1}',
                    '{random.choice(zone_types)}',
                    {random.randint(500, 2000)},
                    {random.uniform(-20, 30):.1f},
                    {random.uniform(0, 40):.1f},
                    true
                )
            """)

    # 3. Product Categories (30개)
    # 기존 카테고리(1~5 가정) 하위로 랜덤 생성
    for i in range(30):
        code = f"CAT-EXT-{i+1:03d}"
        op.execute(f"""
            INSERT INTO product_categories (code, name, parent_id, description)
            VALUES (
                '{code}',
                '확장 카테고리 {i+1}',
                {random.randint(1, 4)}, 
                '자동 생성된 추가 카테고리입니다.'
            )
        """)
    
    # 신규 카테고리 ID 조회
    categories = conn.execute(sa.text("SELECT id FROM product_categories WHERE code LIKE 'CAT-EXT-%'")).fetchall()
    category_ids = [row[0] for row in categories]

    # 4. Products (30개)
    units = ['EA', 'BOX', 'KG', 'SET']
    for i in range(30):
        sku = f"PROD-EXT-{i+1:03d}"
        cat_id = random.choice(category_ids) if category_ids else 1
        op.execute(f"""
            INSERT INTO products (sku, name, category_id, description, unit, weight_kg, length_cm, width_cm, height_cm, unit_price, is_active)
            VALUES (
                '{sku}',
                '확장 상품 {i+1}',
                {cat_id},
                '상품 설명 {i+1}',
                '{random.choice(units)}',
                {random.uniform(0.1, 50.0):.2f},
                {random.uniform(10, 100):.1f},
                {random.uniform(10, 100):.1f},
                {random.uniform(10, 100):.1f},
                {random.randint(1000, 100000)},
                true
            )
        """)

    # 신규 상품 ID 조회
    new_products = conn.execute(sa.text("SELECT id FROM products WHERE sku LIKE 'PROD-EXT-%'")).fetchall()
    product_ids = [row[0] for row in new_products]

    # 5. Customers (30개)
    customer_types = ['regular', 'vip', 'wholesale']
    for i in range(30):
        code = f"CUST-EXT-{i+1:03d}"
        op.execute(f"""
            INSERT INTO customers (code, name, contact_name, email, phone, address, city, region, postal_code, customer_type, credit_limit, is_active)
            VALUES (
                '{code}',
                '확장 고객사 {i+1}',
                '담당자 {i+1}',
                'cust{i+1}@example.com',
                '{get_random_phone()}',
                '서울시 강남구 테헤란로 {100+i}',
                '서울',
                '서울',
                '{6000+i:05d}',
                '{random.choice(customer_types)}',
                {random.randint(1000000, 50000000)},
                true
            )
        """)

    # 신규 고객 ID 조회
    new_customers = conn.execute(sa.text("SELECT id FROM customers WHERE code LIKE 'CUST-EXT-%'")).fetchall()
    customer_ids = [row[0] for row in new_customers]

    # 6. Carriers, Vehicles, Drivers (각 30개)
    service_types = ['{express}', '{standard}', '{same_day}', '{express,standard}']
    vehicle_types = ['truck_small', 'truck_medium', 'truck_large', 'van']
    
    carrier_ids = []
    vehicle_ids = []
    driver_ids = []

    for i in range(30):
        # Carrier
        c_code = f"CAR-EXT-{i+1:03d}"
        op.execute(f"""
            INSERT INTO carriers (code, name, contact_name, phone, email, service_types, rating, is_active)
            VALUES (
                '{c_code}',
                '확장 운송사 {i+1}',
                '운송담당 {i+1}',
                '{get_random_phone()}',
                'carrier{i+1}@logistics.com',
                '{random.choice(service_types)}',
                {random.uniform(3.0, 5.0):.1f},
                true
            )
        """)
        
        # We need IDs immediately for linking. In pure SQL script without RETURNING it's hard.
        # But we can query back.
        
    new_carriers = conn.execute(sa.text("SELECT id FROM carriers WHERE code LIKE 'CAR-EXT-%'")).fetchall()
    carrier_ids = [row[0] for row in new_carriers]

    # Vehicles & Drivers
    for i in range(30):
        c_id = random.choice(carrier_ids) if carrier_ids else 1
        
        # Vehicle
        plate = f"EXT{random.randint(1000,9999)}"
        op.execute(f"""
            INSERT INTO vehicles (carrier_id, plate_number, vehicle_type, capacity_kg, capacity_cbm, fuel_type, year, status)
            VALUES (
                {c_id},
                '{plate}',
                '{random.choice(vehicle_types)}',
                {random.randint(1000, 5000)},
                {random.randint(10, 30)},
                'diesel',
                {random.randint(2015, 2024)},
                'available'
            )
        """)
        
        # Driver
        emp_id = f"DRV-EXT-{i+1:03d}"
        op.execute(f"""
            INSERT INTO drivers (employee_id, name, phone, email, license_number, license_type, status, hire_date)
            VALUES (
                '{emp_id}',
                '기사 {i+1}',
                '{get_random_phone()}',
                'driver{i+1}@logistics.com',
                '11-{random.randint(100000, 999999)}',
                '1종대형',
                'active',
                '{get_random_date(days_back=365)}'
            )
        """)

    new_vehicles = conn.execute(sa.text("SELECT id FROM vehicles WHERE plate_number LIKE 'EXT%'")).fetchall()
    vehicle_ids = [row[0] for row in new_vehicles]
    
    new_drivers = conn.execute(sa.text("SELECT id FROM drivers WHERE employee_id LIKE 'DRV-EXT-%'")).fetchall()
    driver_ids = [row[0] for row in new_drivers]

    # 7. Inventory (30개)
    # 신규 상품과 신규 창고 매핑
    if product_ids and warehouse_ids:
        for i in range(30):
            p_id = random.choice(product_ids)
            w_id = random.choice(warehouse_ids)
            op.execute(f"""
                INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, lot_number, expiry_date, last_counted_at)
                VALUES (
                    {p_id},
                    {w_id},
                    {random.randint(10, 1000)},
                    0,
                    'LOT-{datetime.now().strftime("%Y%m")}-{i:03d}',
                    '{get_random_date(days_back=-180)}', -- future expiry
                    '{get_random_date(days_back=30)}'
                )
                ON CONFLICT DO NOTHING
            """)

    # 8. Orders (30개)
    order_ids = []
    if customer_ids:
        for i in range(30):
            o_num = f"ORD-EXT-{datetime.now().strftime('%Y%m%d')}-{i+1:03d}"
            c_id = random.choice(customer_ids)
            op.execute(f"""
                INSERT INTO orders (order_number, customer_id, order_date, status, total_amount, shipping_address, shipping_city, shipping_region, shipping_postal_code)
                VALUES (
                    '{o_num}',
                    {c_id},
                    '{get_random_date(days_back=7)}',
                    'pending',
                    {random.randint(50000, 1000000)},
                    '배송지 주소 {i+1}',
                    '서울',
                    '서울',
                    '06000'
                )
            """)
    
    new_orders = conn.execute(sa.text("SELECT id FROM orders WHERE order_number LIKE 'ORD-EXT-%'")).fetchall()
    order_ids = [row[0] for row in new_orders]

    # 9. Order Items
    if order_ids and product_ids:
        for o_id in order_ids:
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                p_id = random.choice(product_ids)
                op.execute(f"""
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                    VALUES (
                        {o_id},
                        {p_id},
                        {random.randint(1, 10)},
                        10000,
                        10000
                    )
                """)

    # 10. Shipments & Routes (30개)
    if order_ids and carrier_ids and vehicle_ids and driver_ids and warehouse_ids:
        for i in range(30):
            ship_num = f"SHP-EXT-{i+1:03d}"
            o_id = random.choice(order_ids)
            c_id = random.choice(carrier_ids)
            v_id = random.choice(vehicle_ids)
            d_id = random.choice(driver_ids)
            w_id = random.choice(warehouse_ids)
            
            op.execute(f"""
                INSERT INTO shipments (shipment_number, order_id, carrier_id, vehicle_id, driver_id, status, origin_warehouse_id, destination_address, estimated_delivery)
                VALUES (
                    '{ship_num}',
                    {o_id},
                    {c_id},
                    {v_id},
                    {d_id},
                    'pending',
                    {w_id},
                    '도착지 주소 {i+1}',
                    '{get_random_date(days_back=-3)}'
                )
            """)
            
            # Route
            route_code = f"RT-EXT-{i+1:03d}"
            op.execute(f"""
                INSERT INTO delivery_routes (route_code, name, vehicle_id, driver_id, route_date, status, total_distance_km, total_stops)
                VALUES (
                    '{route_code}',
                    '경로 {i+1}',
                    {v_id},
                    {d_id},
                    '{datetime.now().strftime("%Y-%m-%d")}',
                    'planned',
                    {random.uniform(10.0, 300.0):.2f},
                    {random.randint(1, 10)}
                )
            """)

def downgrade() -> None:
    # 역순 삭제
    op.execute("DELETE FROM route_stops WHERE id IN (SELECT id FROM route_stops ORDER BY id DESC LIMIT 100)") # Approximation
    op.execute("DELETE FROM delivery_routes WHERE route_code LIKE 'RT-EXT-%'")
    op.execute("DELETE FROM shipments WHERE shipment_number LIKE 'SHP-EXT-%'")
    op.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE order_number LIKE 'ORD-EXT-%')")
    op.execute("DELETE FROM orders WHERE order_number LIKE 'ORD-EXT-%'")
    op.execute("DELETE FROM inventory WHERE lot_number LIKE 'LOT-%'")
    op.execute("DELETE FROM drivers WHERE employee_id LIKE 'DRV-EXT-%'")
    op.execute("DELETE FROM vehicles WHERE plate_number LIKE 'EXT%'")
    op.execute("DELETE FROM carriers WHERE code LIKE 'CAR-EXT-%'")
    op.execute("DELETE FROM customers WHERE code LIKE 'CUST-EXT-%'")
    op.execute("DELETE FROM products WHERE sku LIKE 'PROD-EXT-%'")
    op.execute("DELETE FROM product_categories WHERE code LIKE 'CAT-EXT-%'")
    op.execute("DELETE FROM warehouse_zones WHERE code LIKE 'Z-WH-EXT-%' OR code LIKE 'Z-%'") # Broad pattern for mock
    op.execute("DELETE FROM warehouses WHERE code LIKE 'WH-EXT-%'")
