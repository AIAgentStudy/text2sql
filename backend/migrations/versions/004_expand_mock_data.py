"""Expand mock data + add sales table

Revision ID: 004
Revises: 003
Create Date: 2024-02-01

- sales 테이블 신규 생성
- 기존 목데이터 삭제 후 확장 데이터 재삽입
- 테이블당 20~50건, 날짜는 CURRENT_DATE 기반 상대 날짜 사용
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # 1. 기존 데이터 삭제 (003의 downgrade 로직 재활용)
    # ============================================================
    op.execute("DELETE FROM route_stops;")
    op.execute("DELETE FROM delivery_routes;")
    op.execute("DELETE FROM shipment_items;")
    op.execute("DELETE FROM shipments;")
    op.execute("DELETE FROM vehicles;")
    op.execute("DELETE FROM carriers;")
    op.execute("DELETE FROM order_items;")
    op.execute("DELETE FROM orders;")
    op.execute("DELETE FROM customers;")
    op.execute("DELETE FROM inventory_transactions;")
    op.execute("DELETE FROM inventory;")
    op.execute("DELETE FROM products;")
    op.execute("DELETE FROM product_categories;")
    op.execute("DELETE FROM warehouse_zones;")
    op.execute("DELETE FROM warehouses;")
    op.execute("DELETE FROM drivers;")

    # ID 시퀀스 리셋
    for table in [
        "drivers", "warehouses", "warehouse_zones", "product_categories",
        "products", "inventory", "inventory_transactions", "customers",
        "orders", "order_items", "carriers", "vehicles", "shipments",
        "shipment_items", "delivery_routes", "route_stops",
    ]:
        op.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;")

    # ============================================================
    # 2. sales 테이블 생성
    # ============================================================
    op.execute("""
        CREATE TABLE sales (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            sale_date TIMESTAMP WITH TIME ZONE NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(15, 2) NOT NULL,
            total_amount DECIMAL(15, 2) NOT NULL,
            region VARCHAR(50),
            channel VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX idx_sales_product_id ON sales(product_id)")
    op.execute("CREATE INDEX idx_sales_customer_id ON sales(customer_id)")
    op.execute("CREATE INDEX idx_sales_sale_date ON sales(sale_date)")
    op.execute("CREATE INDEX idx_sales_region ON sales(region)")
    op.execute("CREATE INDEX idx_sales_channel ON sales(channel)")
    op.execute("COMMENT ON TABLE sales IS '매출'")
    op.execute("COMMENT ON COLUMN sales.sale_date IS '매출 일자'")
    op.execute("COMMENT ON COLUMN sales.quantity IS '판매 수량'")
    op.execute("COMMENT ON COLUMN sales.unit_price IS '단가'")
    op.execute("COMMENT ON COLUMN sales.total_amount IS '총 매출액'")
    op.execute("COMMENT ON COLUMN sales.region IS '판매 지역'")
    op.execute("COMMENT ON COLUMN sales.channel IS '판매 채널 (online, offline, wholesale)'")

    # sales 테이블 권한 추가
    op.execute("""
        INSERT INTO table_permissions (role_id, table_name, can_read, can_write)
        SELECT r.id, 'sales', TRUE, TRUE
        FROM roles r
        WHERE r.name IN ('admin', 'manager');
    """)

    # ============================================================
    # 3. 확장 목데이터 삽입
    # ============================================================

    # === Drivers (기사 정보) - 기존 10명 유지 ===
    op.execute("""
        INSERT INTO drivers (employee_id, name, phone, email, license_number, license_type, license_expiry, hire_date, status, address) VALUES
        ('DRV001', '김철수', '010-1234-5678', 'kim.cs@logistics.com', '11-12-345678-90', '1종대형', '2025-06-15', '2020-03-01', 'active', '서울시 강남구 역삼동 123'),
        ('DRV002', '이영희', '010-2345-6789', 'lee.yh@logistics.com', '22-23-456789-01', '1종대형', '2025-08-20', '2019-07-15', 'active', '서울시 서초구 서초동 456'),
        ('DRV003', '박민수', '010-3456-7890', 'park.ms@logistics.com', '33-34-567890-12', '1종보통', '2024-12-01', '2021-01-10', 'active', '경기도 성남시 분당구 정자동 789'),
        ('DRV004', '정수진', '010-4567-8901', 'jung.sj@logistics.com', '44-45-678901-23', '1종대형', '2025-03-30', '2018-09-20', 'active', '인천시 남동구 논현동 101'),
        ('DRV005', '최동현', '010-5678-9012', 'choi.dh@logistics.com', '55-56-789012-34', '1종대형', '2025-11-15', '2022-02-28', 'active', '경기도 수원시 영통구 영통동 202'),
        ('DRV006', '한지민', '010-6789-0123', 'han.jm@logistics.com', '66-67-890123-45', '1종보통', '2024-09-10', '2020-06-01', 'on_leave', '서울시 송파구 잠실동 303'),
        ('DRV007', '윤성호', '010-7890-1234', 'yoon.sh@logistics.com', '77-78-901234-56', '1종대형', '2025-04-25', '2019-11-15', 'active', '경기도 고양시 일산동구 백석동 404'),
        ('DRV008', '강미영', '010-8901-2345', 'kang.my@logistics.com', '88-89-012345-67', '1종대형', '2025-07-08', '2021-08-01', 'active', '부산시 해운대구 우동 505'),
        ('DRV009', '조현우', '010-9012-3456', 'cho.hw@logistics.com', '99-90-123456-78', '1종보통', '2024-10-20', '2022-04-15', 'active', '대구시 수성구 범어동 606'),
        ('DRV010', '임서연', '010-0123-4567', 'lim.sy@logistics.com', '00-01-234567-89', '1종대형', '2025-12-31', '2023-01-02', 'active', '광주시 서구 치평동 707');
    """)

    # === Warehouses (창고) - 기존 10개 유지 ===
    op.execute("""
        INSERT INTO warehouses (code, name, address, city, region, postal_code, phone, manager_name, capacity_sqm, is_active) VALUES
        ('WH-ICN01', '인천 물류센터', '인천시 중구 운서동 공항대로 123', '인천', '인천광역시', '22382', '032-123-4567', '김물류', 15000.00, TRUE),
        ('WH-SEL01', '서울 중앙 물류센터', '서울시 금천구 가산디지털로 456', '서울', '서울특별시', '08589', '02-234-5678', '이센터', 8000.00, TRUE),
        ('WH-BSN01', '부산 항만 물류센터', '부산시 강서구 송정동 항만대로 789', '부산', '부산광역시', '46722', '051-345-6789', '박항만', 20000.00, TRUE),
        ('WH-GYG01', '경기 남부 물류센터', '경기도 용인시 처인구 물류로 101', '용인', '경기도', '17019', '031-456-7890', '최경기', 12000.00, TRUE),
        ('WH-DGU01', '대구 물류센터', '대구시 달서구 성서공단로 202', '대구', '대구광역시', '42704', '053-567-8901', '정대구', 10000.00, TRUE),
        ('WH-GWJ01', '광주 물류센터', '광주시 광산구 첨단과기로 303', '광주', '광주광역시', '62234', '062-678-9012', '한광주', 7000.00, TRUE),
        ('WH-DJN01', '대전 물류센터', '대전시 유성구 테크노중앙로 404', '대전', '대전광역시', '34129', '042-789-0123', '윤대전', 9000.00, TRUE),
        ('WH-ICN02', '인천 냉동 물류센터', '인천시 서구 청라동 냉동로 505', '인천', '인천광역시', '22745', '032-890-1234', '강냉동', 5000.00, TRUE),
        ('WH-SEL02', '서울 동부 물류센터', '서울시 송파구 문정동 물류단지로 606', '서울', '서울특별시', '05836', '02-901-2345', '조동부', 6000.00, TRUE),
        ('WH-JJU01', '제주 물류센터', '제주시 애월읍 물류대로 707', '제주', '제주특별자치도', '63064', '064-012-3456', '임제주', 4000.00, TRUE);
    """)

    # === Warehouse Zones (창고 구역) - 기존 10개 유지 ===
    op.execute("""
        INSERT INTO warehouse_zones (warehouse_id, code, name, zone_type, capacity_units, temperature_min, temperature_max, is_active) VALUES
        (1, 'A1', 'A구역 1층', '일반', 5000, NULL, NULL, TRUE),
        (1, 'A2', 'A구역 2층', '일반', 5000, NULL, NULL, TRUE),
        (1, 'B1', 'B구역 냉장', '냉장', 2000, 2.00, 8.00, TRUE),
        (2, 'C1', 'C구역 일반', '일반', 3000, NULL, NULL, TRUE),
        (2, 'C2', 'C구역 위험물', '위험물', 500, NULL, NULL, TRUE),
        (3, 'D1', 'D구역 컨테이너', '일반', 8000, NULL, NULL, TRUE),
        (3, 'D2', 'D구역 냉동', '냉동', 3000, -25.00, -18.00, TRUE),
        (4, 'E1', 'E구역 대형화물', '일반', 4000, NULL, NULL, TRUE),
        (5, 'F1', 'F구역 일반', '일반', 3500, NULL, NULL, TRUE),
        (8, 'G1', 'G구역 냉동', '냉동', 2500, -25.00, -18.00, TRUE);
    """)

    # === Product Categories (제품 카테고리) - 기존 10개 + 4개 추가 ===
    op.execute("""
        INSERT INTO product_categories (code, name, parent_id, description) VALUES
        ('ELEC', '전자제품', NULL, '전자기기 및 부품'),
        ('FOOD', '식품', NULL, '식료품 및 음료'),
        ('CLTH', '의류', NULL, '의류 및 패션 잡화'),
        ('FURN', '가구', NULL, '가구 및 인테리어'),
        ('ELEC-MOB', '모바일기기', 1, '스마트폰, 태블릿 등'),
        ('ELEC-PC', '컴퓨터', 1, 'PC, 노트북, 주변기기'),
        ('FOOD-FRZ', '냉동식품', 2, '냉동 보관 식품'),
        ('FOOD-BEV', '음료', 2, '음료 및 주류'),
        ('CLTH-MEN', '남성의류', 3, '남성 의류'),
        ('FURN-OFF', '사무가구', 4, '사무용 가구'),
        ('COSM', '화장품', NULL, '화장품 및 뷰티'),
        ('HLTH', '건강식품', NULL, '건강 보조식품'),
        ('LIFE', '생활용품', NULL, '생활 잡화'),
        ('CLTH-WOM', '여성의류', 3, '여성 의류');
    """)

    # === Products (제품) - 10 → 30개 ===
    op.execute("""
        INSERT INTO products (sku, name, category_id, description, unit, weight_kg, length_cm, width_cm, height_cm, unit_price, is_active) VALUES
        ('SKU-MOB-001', '스마트폰 X100', 5, '최신 플래그십 스마트폰', 'EA', 0.185, 15.00, 7.50, 0.80, 1200000.00, TRUE),
        ('SKU-MOB-002', '태블릿 T500', 5, '10인치 태블릿', 'EA', 0.450, 25.00, 17.00, 0.70, 800000.00, TRUE),
        ('SKU-PC-001', '노트북 L300', 6, '15인치 비즈니스 노트북', 'EA', 1.800, 36.00, 25.00, 2.00, 1500000.00, TRUE),
        ('SKU-PC-002', '무선마우스 M100', 6, '인체공학 무선마우스', 'EA', 0.095, 12.00, 7.00, 4.00, 45000.00, TRUE),
        ('SKU-FRZ-001', '냉동만두 1kg', 7, '수제 냉동만두', 'BOX', 1.050, 25.00, 15.00, 8.00, 12000.00, TRUE),
        ('SKU-FRZ-002', '냉동피자 400g', 7, '이탈리안 냉동피자', 'BOX', 0.450, 30.00, 30.00, 3.00, 8500.00, TRUE),
        ('SKU-BEV-001', '생수 2L (6입)', 8, '미네랄 생수 묶음', 'BOX', 12.500, 30.00, 20.00, 32.00, 5500.00, TRUE),
        ('SKU-MEN-001', '남성 캐주얼 셔츠', 9, '면 100% 캐주얼 셔츠', 'EA', 0.300, 40.00, 30.00, 2.00, 59000.00, TRUE),
        ('SKU-OFF-001', '사무용 의자 EC200', 10, '인체공학 사무용 의자', 'EA', 15.000, 65.00, 65.00, 120.00, 350000.00, TRUE),
        ('SKU-OFF-002', '책상 D500', 10, '1400mm 사무용 책상', 'EA', 35.000, 140.00, 70.00, 75.00, 250000.00, TRUE),
        ('SKU-COSM-001', '수분 크림 50ml', 11, '히알루론산 수분 크림', 'EA', 0.120, 8.00, 8.00, 6.00, 38000.00, TRUE),
        ('SKU-COSM-002', '선크림 SPF50', 11, '자외선 차단 크림', 'EA', 0.080, 6.00, 4.00, 15.00, 25000.00, TRUE),
        ('SKU-COSM-003', '클렌징 오일 200ml', 11, '딥 클렌징 오일', 'EA', 0.250, 7.00, 7.00, 18.00, 22000.00, TRUE),
        ('SKU-HLTH-001', '종합비타민 90정', 12, '멀티비타민 3개월분', 'EA', 0.150, 7.00, 7.00, 12.00, 35000.00, TRUE),
        ('SKU-HLTH-002', '프로바이오틱스 60캡슐', 12, '유산균 2개월분', 'EA', 0.100, 6.00, 6.00, 10.00, 42000.00, TRUE),
        ('SKU-HLTH-003', '오메가3 120캡슐', 12, '순수 오메가3 4개월분', 'EA', 0.200, 8.00, 8.00, 14.00, 55000.00, TRUE),
        ('SKU-LIFE-001', '주방세제 1L', 13, '친환경 주방 세제', 'EA', 1.050, 10.00, 8.00, 25.00, 8900.00, TRUE),
        ('SKU-LIFE-002', '섬유유연제 2L', 13, '프리미엄 섬유유연제', 'EA', 2.100, 12.00, 10.00, 30.00, 12500.00, TRUE),
        ('SKU-LIFE-003', '핸드워시 500ml', 13, '항균 핸드워시', 'EA', 0.550, 8.00, 6.00, 20.00, 6500.00, TRUE),
        ('SKU-WOM-001', '여성 블라우스', 14, '실크 블렌드 블라우스', 'EA', 0.250, 40.00, 30.00, 2.00, 69000.00, TRUE),
        ('SKU-WOM-002', '여성 슬랙스', 14, '스트레치 슬랙스', 'EA', 0.400, 50.00, 35.00, 3.00, 55000.00, TRUE),
        ('SKU-MOB-003', '스마트워치 W200', 5, '헬스 트래킹 스마트워치', 'EA', 0.060, 5.00, 5.00, 1.50, 450000.00, TRUE),
        ('SKU-PC-003', '27인치 모니터', 6, '4K UHD 모니터', 'EA', 6.500, 62.00, 20.00, 45.00, 550000.00, TRUE),
        ('SKU-FRZ-003', '냉동새우 500g', 7, '손질 냉동새우', 'BOX', 0.550, 20.00, 15.00, 5.00, 15000.00, TRUE),
        ('SKU-BEV-002', '오렌지주스 1L (4입)', 8, '100% 오렌지주스', 'BOX', 4.200, 25.00, 25.00, 28.00, 12000.00, TRUE),
        ('SKU-MEN-002', '남성 수트 자켓', 9, '슬림핏 수트 자켓', 'EA', 0.800, 60.00, 45.00, 5.00, 290000.00, TRUE),
        ('SKU-COSM-004', '에센스 30ml', 11, '레티놀 에센스', 'EA', 0.100, 5.00, 5.00, 12.00, 48000.00, TRUE),
        ('SKU-HLTH-004', '콜라겐 파우더 300g', 12, '저분자 콜라겐', 'EA', 0.350, 10.00, 10.00, 15.00, 39000.00, TRUE),
        ('SKU-LIFE-004', '욕실 세정제 750ml', 13, '곰팡이 제거 세정제', 'EA', 0.800, 8.00, 6.00, 28.00, 7500.00, TRUE),
        ('SKU-OFF-003', '파일 캐비닛 3단', 10, '잠금장치 파일 캐비닛', 'EA', 25.000, 47.00, 62.00, 103.00, 180000.00, TRUE);
    """)

    # === Inventory (재고) - 30개 ===
    op.execute("""
        INSERT INTO inventory (product_id, warehouse_id, zone_id, quantity, reserved_quantity, lot_number, expiry_date) VALUES
        (1, 1, 1, 500, 50, 'LOT-2024-001', NULL),
        (2, 1, 1, 300, 30, 'LOT-2024-002', NULL),
        (3, 2, 4, 150, 20, 'LOT-2024-003', NULL),
        (4, 2, 4, 1000, 100, 'LOT-2024-004', NULL),
        (5, 8, 10, 800, 80, 'LOT-2024-005', '2025-06-30'),
        (6, 8, 10, 600, 60, 'LOT-2024-006', '2025-04-15'),
        (7, 1, 1, 2000, 200, 'LOT-2024-007', '2026-12-31'),
        (8, 4, 8, 400, 40, 'LOT-2024-008', NULL),
        (9, 4, 8, 100, 10, 'LOT-2024-009', NULL),
        (10, 4, 8, 80, 8, 'LOT-2024-010', NULL),
        (11, 2, 4, 1200, 150, 'LOT-2024-011', NULL),
        (12, 2, 4, 900, 100, 'LOT-2024-012', NULL),
        (13, 2, 4, 600, 80, 'LOT-2024-013', NULL),
        (14, 1, 1, 3000, 500, 'LOT-2024-014', '2026-06-30'),
        (15, 1, 1, 2500, 400, 'LOT-2024-015', '2026-08-31'),
        (16, 1, 1, 1800, 300, 'LOT-2024-016', '2026-10-31'),
        (17, 3, 6, 5000, 800, 'LOT-2024-017', NULL),
        (18, 3, 6, 3000, 600, 'LOT-2024-018', NULL),
        (19, 3, 6, 4000, 700, 'LOT-2024-019', NULL),
        (20, 4, 8, 350, 50, 'LOT-2024-020', NULL),
        (21, 4, 8, 280, 40, 'LOT-2024-021', NULL),
        (22, 1, 1, 200, 30, 'LOT-2024-022', NULL),
        (23, 2, 4, 80, 10, 'LOT-2024-023', NULL),
        (24, 8, 10, 400, 60, 'LOT-2024-024', '2025-08-31'),
        (25, 1, 1, 1500, 200, 'LOT-2024-025', '2026-12-31'),
        (26, 4, 8, 60, 5, 'LOT-2024-026', NULL),
        (27, 2, 4, 700, 100, 'LOT-2024-027', NULL),
        (28, 1, 1, 2200, 350, 'LOT-2024-028', '2026-09-30'),
        (29, 3, 6, 6000, 5950, 'LOT-2024-029', NULL),
        (30, 4, 8, 45, 40, 'LOT-2024-030', NULL);
    """)

    # === Inventory Transactions (재고 이력) ===
    op.execute("""
        INSERT INTO inventory_transactions (inventory_id, transaction_type, quantity, reference_type, reference_id, notes) VALUES
        (1, 'IN', 500, 'PURCHASE', 1001, '초기 입고'),
        (2, 'IN', 300, 'PURCHASE', 1002, '초기 입고'),
        (3, 'IN', 200, 'PURCHASE', 1003, '초기 입고'),
        (1, 'OUT', -50, 'ORDER', 1, '주문 출고'),
        (4, 'IN', 1000, 'PURCHASE', 1004, '대량 입고'),
        (5, 'IN', 1000, 'PURCHASE', 1005, '냉동식품 입고'),
        (5, 'OUT', -200, 'ORDER', 2, '주문 출고'),
        (6, 'IN', 600, 'PURCHASE', 1006, '냉동피자 입고'),
        (7, 'ADJUST', -50, 'ADJUSTMENT', 2001, '재고실사 조정'),
        (8, 'IN', 400, 'PURCHASE', 1007, '의류 입고'),
        (11, 'IN', 1200, 'PURCHASE', 1008, '화장품 입고'),
        (14, 'IN', 3000, 'PURCHASE', 1009, '건강식품 입고'),
        (17, 'IN', 5000, 'PURCHASE', 1010, '생활용품 대량 입고'),
        (29, 'OUT', -5900, 'ORDER', 10, '대량 출고 - 재고 부족 상황'),
        (30, 'OUT', -35, 'ORDER', 11, '출고 - 재고 부족 임박');
    """)

    # === Customers (고객) - 10 → 20개 ===
    op.execute("""
        INSERT INTO customers (code, name, contact_name, email, phone, address, city, region, postal_code, customer_type, credit_limit, is_active) VALUES
        ('CUST-001', '삼성물산', '김삼성', 'samsung@example.com', '02-1234-5678', '서울시 강남구 삼성동 159', '서울', '서울특별시', '06288', 'vip', 500000000.00, TRUE),
        ('CUST-002', '현대백화점', '이현대', 'hyundai@example.com', '02-2345-6789', '서울시 강남구 압구정로 165', '서울', '서울특별시', '06001', 'vip', 300000000.00, TRUE),
        ('CUST-003', '롯데마트', '박롯데', 'lotte@example.com', '02-3456-7890', '서울시 송파구 올림픽로 240', '서울', '서울특별시', '05551', 'vip', 400000000.00, TRUE),
        ('CUST-004', '이마트', '최이마트', 'emart@example.com', '02-4567-8901', '서울시 성동구 왕십리로 83', '서울', '서울특별시', '04763', 'vip', 350000000.00, TRUE),
        ('CUST-005', '쿠팡', '정쿠팡', 'coupang@example.com', '02-5678-9012', '서울시 송파구 송파대로 570', '서울', '서울특별시', '05855', 'vip', 600000000.00, TRUE),
        ('CUST-006', '네이버쇼핑', '한네이버', 'naver@example.com', '031-6789-0123', '경기도 성남시 분당구 정자일로 95', '성남', '경기도', '13561', 'wholesale', 200000000.00, TRUE),
        ('CUST-007', '카카오커머스', '윤카카오', 'kakao@example.com', '064-7890-1234', '제주시 첨단로 242', '제주', '제주특별자치도', '63309', 'wholesale', 150000000.00, TRUE),
        ('CUST-008', '마켓컬리', '강컬리', 'kurly@example.com', '02-8901-2345', '서울시 서초구 헌릉로 8', '서울', '서울특별시', '06796', 'regular', 100000000.00, TRUE),
        ('CUST-009', 'GS리테일', '조GS', 'gs@example.com', '02-9012-3456', '서울시 강남구 논현로 508', '서울', '서울특별시', '06141', 'vip', 250000000.00, TRUE),
        ('CUST-010', 'BGF리테일', '임BGF', 'bgf@example.com', '02-0123-4567', '서울시 강남구 테헤란로 405', '서울', '서울특별시', '06168', 'wholesale', 180000000.00, TRUE),
        ('CUST-011', '올리브영', '김올리브', 'oliveyoung@example.com', '02-1111-2222', '서울시 강남구 도산대로 123', '서울', '서울특별시', '06038', 'vip', 280000000.00, TRUE),
        ('CUST-012', '무신사', '이무신사', 'musinsa@example.com', '02-2222-3333', '서울시 성동구 아차산로 126', '서울', '서울특별시', '04790', 'wholesale', 150000000.00, TRUE),
        ('CUST-013', '부산마트', '박부산', 'busanmart@example.com', '051-3333-4444', '부산시 해운대구 해운대로 456', '부산', '부산광역시', '48094', 'regular', 80000000.00, TRUE),
        ('CUST-014', '대구유통', '최대구', 'daegu@example.com', '053-4444-5555', '대구시 수성구 범어로 789', '대구', '대구광역시', '42019', 'regular', 60000000.00, TRUE),
        ('CUST-015', '인천쇼핑', '정인천', 'incheon@example.com', '032-5555-6666', '인천시 남동구 경인로 321', '인천', '인천광역시', '21570', 'regular', 70000000.00, TRUE),
        ('CUST-016', '광주유통', '한광주', 'gwangju@example.com', '062-6666-7777', '광주시 서구 상무대로 654', '광주', '광주광역시', '61945', 'regular', 50000000.00, TRUE),
        ('CUST-017', '대전마켓', '윤대전', 'daejeon@example.com', '042-7777-8888', '대전시 유성구 대학로 987', '대전', '대전광역시', '34134', 'regular', 55000000.00, TRUE),
        ('CUST-018', '수원유통', '강수원', 'suwon@example.com', '031-8888-9999', '경기도 수원시 팔달구 효원로 147', '수원', '경기도', '16490', 'wholesale', 120000000.00, TRUE),
        ('CUST-019', '성남마켓', '조성남', 'seongnam@example.com', '031-9999-0000', '경기도 성남시 중원구 성남대로 258', '성남', '경기도', '13160', 'regular', 45000000.00, TRUE),
        ('CUST-020', '제주쇼핑', '임제주', 'jejushopping@example.com', '064-0000-1111', '제주시 연동 연북로 369', '제주', '제주특별자치도', '63122', 'regular', 40000000.00, TRUE);
    """)

    # === Orders (주문) - 10 → 30개 (CURRENT_DATE 기반 최근 3개월) ===
    op.execute("""
        INSERT INTO orders (order_number, customer_id, order_date, status, total_amount, shipping_address, shipping_city, shipping_region, shipping_postal_code, notes) VALUES
        ('ORD-2024-00001', 1, CURRENT_TIMESTAMP - INTERVAL '85 days', 'delivered', 60000000.00, '서울시 강남구 삼성동 159', '서울', '서울특별시', '06288', '긴급 배송 요청'),
        ('ORD-2024-00002', 2, CURRENT_TIMESTAMP - INTERVAL '80 days', 'delivered', 24000000.00, '서울시 강남구 압구정로 165', '서울', '서울특별시', '06001', NULL),
        ('ORD-2024-00003', 3, CURRENT_TIMESTAMP - INTERVAL '75 days', 'delivered', 15000000.00, '서울시 송파구 올림픽로 240', '서울', '서울특별시', '05551', '2층 하역장 도착'),
        ('ORD-2024-00004', 4, CURRENT_TIMESTAMP - INTERVAL '70 days', 'delivered', 8500000.00, '서울시 성동구 왕십리로 83', '서울', '서울특별시', '04763', NULL),
        ('ORD-2024-00005', 5, CURRENT_TIMESTAMP - INTERVAL '65 days', 'delivered', 30000000.00, '서울시 송파구 송파대로 570', '서울', '서울특별시', '05855', '대량 주문'),
        ('ORD-2024-00006', 6, CURRENT_TIMESTAMP - INTERVAL '60 days', 'delivered', 12000000.00, '경기도 성남시 분당구 정자일로 95', '성남', '경기도', '13561', NULL),
        ('ORD-2024-00007', 7, CURRENT_TIMESTAMP - INTERVAL '55 days', 'delivered', 5900000.00, '제주시 첨단로 242', '제주', '제주특별자치도', '63309', '도서 지역 배송'),
        ('ORD-2024-00008', 8, CURRENT_TIMESTAMP - INTERVAL '50 days', 'delivered', 3500000.00, '서울시 서초구 헌릉로 8', '서울', '서울특별시', '06796', NULL),
        ('ORD-2024-00009', 9, CURRENT_TIMESTAMP - INTERVAL '45 days', 'delivered', 17500000.00, '서울시 강남구 논현로 508', '서울', '서울특별시', '06141', NULL),
        ('ORD-2024-00010', 10, CURRENT_TIMESTAMP - INTERVAL '40 days', 'delivered', 22000000.00, '서울시 강남구 테헤란로 405', '서울', '서울특별시', '06168', NULL),
        ('ORD-2024-00011', 11, CURRENT_TIMESTAMP - INTERVAL '35 days', 'delivered', 8500000.00, '서울시 강남구 도산대로 123', '서울', '서울특별시', '06038', '올리브영 정기 주문'),
        ('ORD-2024-00012', 12, CURRENT_TIMESTAMP - INTERVAL '32 days', 'delivered', 15200000.00, '서울시 성동구 아차산로 126', '서울', '서울특별시', '04790', NULL),
        ('ORD-2024-00013', 13, CURRENT_TIMESTAMP - INTERVAL '28 days', 'shipped', 9800000.00, '부산시 해운대구 해운대로 456', '부산', '부산광역시', '48094', NULL),
        ('ORD-2024-00014', 14, CURRENT_TIMESTAMP - INTERVAL '25 days', 'shipped', 4500000.00, '대구시 수성구 범어로 789', '대구', '대구광역시', '42019', NULL),
        ('ORD-2024-00015', 1, CURRENT_TIMESTAMP - INTERVAL '22 days', 'shipped', 45000000.00, '서울시 강남구 삼성동 159', '서울', '서울특별시', '06288', '2차 주문'),
        ('ORD-2024-00016', 5, CURRENT_TIMESTAMP - INTERVAL '20 days', 'processing', 28000000.00, '서울시 송파구 송파대로 570', '서울', '서울특별시', '05855', NULL),
        ('ORD-2024-00017', 15, CURRENT_TIMESTAMP - INTERVAL '18 days', 'processing', 6700000.00, '인천시 남동구 경인로 321', '인천', '인천광역시', '21570', NULL),
        ('ORD-2024-00018', 16, CURRENT_TIMESTAMP - INTERVAL '15 days', 'confirmed', 3200000.00, '광주시 서구 상무대로 654', '광주', '광주광역시', '61945', NULL),
        ('ORD-2024-00019', 17, CURRENT_TIMESTAMP - INTERVAL '12 days', 'confirmed', 4800000.00, '대전시 유성구 대학로 987', '대전', '대전광역시', '34134', NULL),
        ('ORD-2024-00020', 18, CURRENT_TIMESTAMP - INTERVAL '10 days', 'confirmed', 18500000.00, '경기도 수원시 팔달구 효원로 147', '수원', '경기도', '16490', '대량 주문'),
        ('ORD-2024-00021', 3, CURRENT_TIMESTAMP - INTERVAL '8 days', 'pending', 12000000.00, '서울시 송파구 올림픽로 240', '서울', '서울특별시', '05551', NULL),
        ('ORD-2024-00022', 11, CURRENT_TIMESTAMP - INTERVAL '7 days', 'pending', 9500000.00, '서울시 강남구 도산대로 123', '서울', '서울특별시', '06038', NULL),
        ('ORD-2024-00023', 19, CURRENT_TIMESTAMP - INTERVAL '6 days', 'pending', 2100000.00, '경기도 성남시 중원구 성남대로 258', '성남', '경기도', '13160', NULL),
        ('ORD-2024-00024', 2, CURRENT_TIMESTAMP - INTERVAL '5 days', 'pending', 35000000.00, '서울시 강남구 압구정로 165', '서울', '서울특별시', '06001', NULL),
        ('ORD-2024-00025', 20, CURRENT_TIMESTAMP - INTERVAL '4 days', 'pending', 1500000.00, '제주시 연동 연북로 369', '제주', '제주특별자치도', '63122', '도서 지역'),
        ('ORD-2024-00026', 9, CURRENT_TIMESTAMP - INTERVAL '3 days', 'pending', 7800000.00, '서울시 강남구 논현로 508', '서울', '서울특별시', '06141', NULL),
        ('ORD-2024-00027', 4, CURRENT_TIMESTAMP - INTERVAL '2 days', 'pending', 5600000.00, '서울시 성동구 왕십리로 83', '서울', '서울특별시', '04763', NULL),
        ('ORD-2024-00028', 6, CURRENT_TIMESTAMP - INTERVAL '1 day', 'pending', 11000000.00, '경기도 성남시 분당구 정자일로 95', '성남', '경기도', '13561', '긴급'),
        ('ORD-2024-00029', 8, CURRENT_TIMESTAMP - INTERVAL '45 days', 'cancelled', 4200000.00, '서울시 서초구 헌릉로 8', '서울', '서울특별시', '06796', '고객 요청 취소'),
        ('ORD-2024-00030', 7, CURRENT_TIMESTAMP - INTERVAL '38 days', 'cancelled', 2800000.00, '제주시 첨단로 242', '제주', '제주특별자치도', '63309', '재고 부족 취소');
    """)

    # === Order Items (주문 상세) - 확장 ===
    op.execute("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent, line_total) VALUES
        (1, 1, 50, 1200000.00, 0, 60000000.00),
        (2, 2, 30, 800000.00, 0, 24000000.00),
        (3, 3, 10, 1500000.00, 0, 15000000.00),
        (4, 5, 500, 12000.00, 0, 6000000.00),
        (4, 6, 300, 8500.00, 2.94, 2500000.00),
        (5, 1, 20, 1200000.00, 0, 24000000.00),
        (5, 4, 200, 45000.00, 33.33, 6000000.00),
        (6, 8, 200, 59000.00, 1.69, 11800000.00),
        (7, 8, 100, 59000.00, 0, 5900000.00),
        (8, 9, 10, 350000.00, 0, 3500000.00),
        (9, 1, 10, 1200000.00, 0, 12000000.00),
        (9, 22, 10, 550000.00, 0, 5500000.00),
        (10, 3, 12, 1500000.00, 0, 18000000.00),
        (10, 4, 100, 45000.00, 2.22, 4000000.00),
        (11, 11, 100, 38000.00, 0, 3800000.00),
        (11, 12, 100, 25000.00, 0, 2500000.00),
        (11, 13, 100, 22000.00, 0, 2200000.00),
        (12, 20, 100, 69000.00, 0, 6900000.00),
        (12, 21, 150, 55000.00, 0, 8250000.00),
        (13, 5, 300, 12000.00, 0, 3600000.00),
        (13, 6, 200, 8500.00, 0, 1700000.00),
        (13, 24, 150, 15000.00, 0, 2250000.00),
        (13, 25, 100, 12000.00, 0, 1200000.00),
        (14, 14, 50, 35000.00, 0, 1750000.00),
        (14, 15, 50, 42000.00, 0, 2100000.00),
        (15, 1, 30, 1200000.00, 0, 36000000.00),
        (15, 22, 20, 450000.00, 0, 9000000.00),
        (16, 3, 15, 1500000.00, 0, 22500000.00),
        (16, 23, 10, 550000.00, 0, 5500000.00),
        (17, 17, 300, 8900.00, 0, 2670000.00),
        (17, 18, 200, 12500.00, 0, 2500000.00),
        (17, 19, 250, 6500.00, 0, 1625000.00),
        (18, 7, 200, 5500.00, 0, 1100000.00),
        (18, 25, 100, 12000.00, 0, 1200000.00),
        (19, 14, 60, 35000.00, 0, 2100000.00),
        (19, 16, 50, 55000.00, 0, 2750000.00),
        (20, 1, 10, 1200000.00, 0, 12000000.00),
        (20, 26, 20, 290000.00, 0, 5800000.00),
        (21, 11, 150, 38000.00, 0, 5700000.00),
        (21, 27, 150, 48000.00, 5.56, 6300000.00),
        (22, 12, 200, 25000.00, 0, 5000000.00),
        (22, 13, 200, 22000.00, 0, 4400000.00),
        (23, 17, 100, 8900.00, 0, 890000.00),
        (23, 19, 200, 6500.00, 7.69, 1200000.00),
        (24, 3, 20, 1500000.00, 0, 30000000.00),
        (24, 4, 100, 45000.00, 0, 4500000.00),
        (25, 7, 100, 5500.00, 0, 550000.00),
        (25, 24, 60, 15000.00, 0, 900000.00),
        (26, 14, 80, 35000.00, 0, 2800000.00),
        (26, 28, 100, 39000.00, 0, 3900000.00),
        (27, 5, 200, 12000.00, 0, 2400000.00),
        (27, 6, 150, 8500.00, 0, 1275000.00),
        (27, 24, 120, 15000.00, 0, 1800000.00),
        (28, 20, 80, 69000.00, 0, 5520000.00),
        (28, 21, 100, 55000.00, 0, 5500000.00);
    """)

    # === Carriers (운송사) - 기존 10개 유지 ===
    op.execute("""
        INSERT INTO carriers (code, name, contact_name, phone, email, service_types, rating, is_active) VALUES
        ('CR-001', 'CJ대한통운', '김대한', '02-1588-1255', 'cj@logistics.com', ARRAY['express', 'standard', 'same_day'], 4.5, TRUE),
        ('CR-002', '롯데택배', '이롯데', '02-1588-2121', 'lotte@logistics.com', ARRAY['express', 'standard'], 4.3, TRUE),
        ('CR-003', '한진택배', '박한진', '02-1588-0011', 'hanjin@logistics.com', ARRAY['express', 'standard', 'economy'], 4.2, TRUE),
        ('CR-004', '로젠택배', '최로젠', '02-1588-9988', 'logen@logistics.com', ARRAY['standard', 'economy'], 4.0, TRUE),
        ('CR-005', '우체국택배', '정우체국', '02-1588-1300', 'koreapost@logistics.com', ARRAY['standard', 'economy'], 4.1, TRUE),
        ('CR-006', '쿠팡로지스틱스', '한쿠팡', '02-1670-7910', 'coupang@logistics.com', ARRAY['express', 'same_day', 'rocket'], 4.7, TRUE),
        ('CR-007', '마켓컬리배송', '윤컬리', '02-1644-1107', 'kurly@logistics.com', ARRAY['same_day', 'dawn'], 4.6, TRUE),
        ('CR-008', '경동택배', '강경동', '02-1588-4577', 'kdexp@logistics.com', ARRAY['standard', 'economy'], 3.9, TRUE),
        ('CR-009', '일양로지스', '조일양', '02-1588-0002', 'ilyang@logistics.com', ARRAY['standard'], 3.8, TRUE),
        ('CR-010', '천일택배', '임천일', '02-1588-2211', 'chunil@logistics.com', ARRAY['standard', 'freight'], 4.0, TRUE);
    """)

    # === Vehicles (차량) - 기존 10대 유지 ===
    op.execute("""
        INSERT INTO vehicles (carrier_id, plate_number, vehicle_type, capacity_kg, capacity_cbm, fuel_type, year, status, last_maintenance, next_maintenance) VALUES
        (1, '서울12가3456', 'truck_large', 5000.00, 30.00, 'diesel', 2022, 'available', '2024-01-10', '2024-04-10'),
        (1, '서울34나5678', 'truck_medium', 2500.00, 15.00, 'diesel', 2021, 'in_use', '2024-01-05', '2024-04-05'),
        (2, '경기56다7890', 'truck_large', 5000.00, 30.00, 'diesel', 2023, 'available', '2024-01-15', '2024-04-15'),
        (2, '인천78라9012', 'van', 1000.00, 8.00, 'gasoline', 2022, 'available', '2024-01-08', '2024-04-08'),
        (3, '부산90마1234', 'truck_large', 8000.00, 45.00, 'diesel', 2020, 'maintenance', '2024-01-20', '2024-02-20'),
        (4, '대구12바3456', 'truck_small', 1500.00, 10.00, 'diesel', 2021, 'available', '2024-01-12', '2024-04-12'),
        (5, '광주34사5678', 'truck_medium', 2500.00, 15.00, 'diesel', 2022, 'in_use', '2024-01-07', '2024-04-07'),
        (6, '서울56아6789', 'van', 800.00, 6.00, 'electric', 2023, 'available', '2024-01-18', '2024-07-18'),
        (7, '서울78자7890', 'truck_small', 1200.00, 8.00, 'electric', 2023, 'available', '2024-01-16', '2024-07-16'),
        (8, '대전90차8901', 'truck_large', 6000.00, 35.00, 'diesel', 2019, 'available', '2024-01-03', '2024-04-03');
    """)

    # === Shipments (배송) - 확장 ===
    op.execute("""
        INSERT INTO shipments (shipment_number, order_id, carrier_id, vehicle_id, driver_id, status, origin_warehouse_id, destination_address, destination_city, destination_region, destination_postal_code, estimated_delivery, actual_delivery, shipping_cost, tracking_number, notes) VALUES
        ('SHP-2024-00001', 1, 1, 1, 1, 'delivered', 1, '서울시 강남구 삼성동 159', '서울', '서울특별시', '06288', CURRENT_TIMESTAMP - INTERVAL '84 days', CURRENT_TIMESTAMP - INTERVAL '84 days' + INTERVAL '5 hours', 50000.00, 'CJ1234567890', '정시 배송 완료'),
        ('SHP-2024-00002', 2, 2, 3, 2, 'delivered', 2, '서울시 강남구 압구정로 165', '서울', '서울특별시', '06001', CURRENT_TIMESTAMP - INTERVAL '79 days', CURRENT_TIMESTAMP - INTERVAL '79 days' + INTERVAL '6 hours', 40000.00, 'LT2345678901', NULL),
        ('SHP-2024-00003', 3, 1, 2, 3, 'delivered', 1, '서울시 송파구 올림픽로 240', '서울', '서울특별시', '05551', CURRENT_TIMESTAMP - INTERVAL '74 days', CURRENT_TIMESTAMP - INTERVAL '74 days' + INTERVAL '4 hours', 45000.00, 'CJ3456789012', NULL),
        ('SHP-2024-00004', 4, 3, 5, 4, 'delivered', 3, '서울시 성동구 왕십리로 83', '서울', '서울특별시', '04763', CURRENT_TIMESTAMP - INTERVAL '69 days', CURRENT_TIMESTAMP - INTERVAL '69 days' + INTERVAL '7 hours', 35000.00, 'HJ4567890123', NULL),
        ('SHP-2024-00005', 5, 6, 8, 5, 'delivered', 1, '서울시 송파구 송파대로 570', '서울', '서울특별시', '05855', CURRENT_TIMESTAMP - INTERVAL '64 days', CURRENT_TIMESTAMP - INTERVAL '64 days' + INTERVAL '3 hours', 30000.00, 'CP5678901234', '로켓배송'),
        ('SHP-2024-00006', 6, 4, 6, 6, 'delivered', 4, '경기도 성남시 분당구 정자일로 95', '성남', '경기도', '13561', CURRENT_TIMESTAMP - INTERVAL '59 days', CURRENT_TIMESTAMP - INTERVAL '59 days' + INTERVAL '5 hours', 25000.00, 'LG6789012345', NULL),
        ('SHP-2024-00007', 7, 5, 7, 7, 'delivered', 10, '제주시 첨단로 242', '제주', '제주특별자치도', '63309', CURRENT_TIMESTAMP - INTERVAL '54 days', CURRENT_TIMESTAMP - INTERVAL '53 days', 80000.00, 'KP7890123456', '항공 운송'),
        ('SHP-2024-00008', 8, 7, 9, 8, 'delivered', 2, '서울시 서초구 헌릉로 8', '서울', '서울특별시', '06796', CURRENT_TIMESTAMP - INTERVAL '49 days', CURRENT_TIMESTAMP - INTERVAL '49 days' + INTERVAL '4 hours', 35000.00, 'KR8901234567', NULL),
        ('SHP-2024-00009', 9, 1, 1, 9, 'delivered', 2, '서울시 강남구 논현로 508', '서울', '서울특별시', '06141', CURRENT_TIMESTAMP - INTERVAL '44 days', CURRENT_TIMESTAMP - INTERVAL '44 days' + INTERVAL '6 hours', 35000.00, 'CJ9012345678', NULL),
        ('SHP-2024-00010', 10, 2, 4, 10, 'delivered', 1, '서울시 강남구 테헤란로 405', '서울', '서울특별시', '06168', CURRENT_TIMESTAMP - INTERVAL '39 days', CURRENT_TIMESTAMP - INTERVAL '39 days' + INTERVAL '5 hours', 40000.00, 'LT0123456789', NULL),
        ('SHP-2024-00011', 11, 1, 2, 1, 'delivered', 2, '서울시 강남구 도산대로 123', '서울', '서울특별시', '06038', CURRENT_TIMESTAMP - INTERVAL '34 days', CURRENT_TIMESTAMP - INTERVAL '34 days' + INTERVAL '4 hours', 30000.00, 'CJ1122334455', NULL),
        ('SHP-2024-00012', 12, 3, 5, 2, 'delivered', 4, '서울시 성동구 아차산로 126', '서울', '서울특별시', '04790', CURRENT_TIMESTAMP - INTERVAL '31 days', CURRENT_TIMESTAMP - INTERVAL '31 days' + INTERVAL '5 hours', 35000.00, 'HJ2233445566', NULL),
        ('SHP-2024-00013', 13, 8, 10, 3, 'in_transit', 3, '부산시 해운대구 해운대로 456', '부산', '부산광역시', '48094', CURRENT_TIMESTAMP - INTERVAL '26 days', NULL, 55000.00, 'KD3344556677', NULL),
        ('SHP-2024-00014', 14, 9, 6, 4, 'in_transit', 5, '대구시 수성구 범어로 789', '대구', '대구광역시', '42019', CURRENT_TIMESTAMP - INTERVAL '23 days', NULL, 45000.00, 'IY4455667788', NULL),
        ('SHP-2024-00015', 15, 1, 1, 5, 'in_transit', 1, '서울시 강남구 삼성동 159', '서울', '서울특별시', '06288', CURRENT_TIMESTAMP - INTERVAL '20 days', NULL, 50000.00, 'CJ5566778899', NULL),
        ('SHP-2024-00016', 16, 6, 8, 6, 'picked_up', 1, '서울시 송파구 송파대로 570', '서울', '서울특별시', '05855', CURRENT_TIMESTAMP - INTERVAL '18 days', NULL, 30000.00, NULL, NULL),
        ('SHP-2024-00017', 17, 4, 6, 7, 'pending', 1, '인천시 남동구 경인로 321', '인천', '인천광역시', '21570', CURRENT_TIMESTAMP - INTERVAL '15 days', NULL, 25000.00, NULL, NULL),
        ('SHP-2024-00018', 20, 2, 3, 8, 'pending', 4, '경기도 수원시 팔달구 효원로 147', '수원', '경기도', '16490', CURRENT_TIMESTAMP - INTERVAL '8 days', NULL, 35000.00, NULL, '대량 배송');
    """)

    # === Shipment Items (배송 상세) ===
    op.execute("""
        INSERT INTO shipment_items (shipment_id, product_id, quantity, picked_quantity) VALUES
        (1, 1, 50, 50),
        (2, 2, 30, 30),
        (3, 3, 10, 10),
        (4, 5, 500, 500),
        (4, 6, 300, 300),
        (5, 1, 20, 20),
        (5, 4, 200, 200),
        (6, 8, 200, 200),
        (7, 8, 100, 100),
        (8, 9, 10, 10),
        (9, 1, 10, 10),
        (9, 22, 10, 10),
        (10, 3, 12, 12),
        (11, 11, 100, 100),
        (11, 12, 100, 100),
        (12, 20, 100, 100),
        (13, 5, 300, 200),
        (13, 6, 200, 150),
        (14, 14, 50, 30),
        (15, 1, 30, 20),
        (16, 3, 15, 0),
        (17, 17, 300, 0),
        (18, 1, 10, 0);
    """)

    # === Delivery Routes (배송 경로) - 10 → 20개 (CURRENT_DATE 기반) ===
    op.execute("""
        INSERT INTO delivery_routes (route_code, name, vehicle_id, driver_id, route_date, status, start_time, end_time, total_distance_km, total_stops) VALUES
        ('RT-2024-001', '강남 1권역 오전', 1, 1, CURRENT_DATE - INTERVAL '84 days', 'completed', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '08:00', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '14:00', 45.5, 8),
        ('RT-2024-002', '강남 2권역 오후', 2, 2, CURRENT_DATE - INTERVAL '84 days', 'completed', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '13:00', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '18:30', 38.2, 6),
        ('RT-2024-003', '송파 1권역', 3, 3, CURRENT_DATE - INTERVAL '74 days', 'completed', (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '09:00', (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '15:00', 52.0, 10),
        ('RT-2024-004', '성동 권역', 5, 4, CURRENT_DATE - INTERVAL '69 days', 'completed', (CURRENT_DATE - INTERVAL '69 days')::timestamp + TIME '08:30', (CURRENT_DATE - INTERVAL '69 days')::timestamp + TIME '14:30', 35.0, 7),
        ('RT-2024-005', '분당 권역', 6, 5, CURRENT_DATE - INTERVAL '59 days', 'completed', (CURRENT_DATE - INTERVAL '59 days')::timestamp + TIME '09:00', (CURRENT_DATE - INTERVAL '59 days')::timestamp + TIME '16:00', 48.5, 9),
        ('RT-2024-006', '서초 1권역', 8, 6, CURRENT_DATE - INTERVAL '49 days', 'completed', (CURRENT_DATE - INTERVAL '49 days')::timestamp + TIME '08:00', (CURRENT_DATE - INTERVAL '49 days')::timestamp + TIME '13:00', 30.0, 5),
        ('RT-2024-007', '제주 권역', 7, 7, CURRENT_DATE - INTERVAL '54 days', 'completed', (CURRENT_DATE - INTERVAL '54 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '54 days')::timestamp + TIME '17:00', 65.0, 4),
        ('RT-2024-008', '강남 3권역', 1, 8, CURRENT_DATE - INTERVAL '44 days', 'completed', (CURRENT_DATE - INTERVAL '44 days')::timestamp + TIME '08:00', (CURRENT_DATE - INTERVAL '44 days')::timestamp + TIME '14:30', 40.0, 7),
        ('RT-2024-009', '강남 4권역', 4, 9, CURRENT_DATE - INTERVAL '39 days', 'completed', (CURRENT_DATE - INTERVAL '39 days')::timestamp + TIME '08:30', (CURRENT_DATE - INTERVAL '39 days')::timestamp + TIME '15:00', 42.5, 8),
        ('RT-2024-010', '강남 5권역', 2, 10, CURRENT_DATE - INTERVAL '34 days', 'completed', (CURRENT_DATE - INTERVAL '34 days')::timestamp + TIME '09:00', (CURRENT_DATE - INTERVAL '34 days')::timestamp + TIME '14:00', 38.0, 6),
        ('RT-2024-011', '부산 해운대 권역', 10, 3, CURRENT_DATE - INTERVAL '27 days', 'in_progress', (CURRENT_DATE - INTERVAL '27 days')::timestamp + TIME '09:00', NULL, 55.0, 8),
        ('RT-2024-012', '대구 수성 권역', 6, 4, CURRENT_DATE - INTERVAL '24 days', 'in_progress', (CURRENT_DATE - INTERVAL '24 days')::timestamp + TIME '08:30', NULL, 40.0, 6),
        ('RT-2024-013', '서울 강남 종합', 1, 5, CURRENT_DATE - INTERVAL '20 days', 'in_progress', (CURRENT_DATE - INTERVAL '20 days')::timestamp + TIME '08:00', NULL, 50.0, 10),
        ('RT-2024-014', '송파 2권역', 8, 6, CURRENT_DATE - INTERVAL '18 days', 'planned', NULL, NULL, 45.0, 7),
        ('RT-2024-015', '인천 남동 권역', 4, 7, CURRENT_DATE - INTERVAL '15 days', 'planned', NULL, NULL, 38.0, 6),
        ('RT-2024-016', '수원 팔달 권역', 3, 8, CURRENT_DATE - INTERVAL '8 days', 'planned', NULL, NULL, 42.0, 8),
        ('RT-2024-017', '서초 2권역', 2, 1, CURRENT_DATE - INTERVAL '5 days', 'planned', NULL, NULL, 32.0, 5),
        ('RT-2024-018', '분당 2권역', 9, 2, CURRENT_DATE - INTERVAL '3 days', 'planned', NULL, NULL, 50.0, 9),
        ('RT-2024-019', '강남 6권역 오전', 1, 9, CURRENT_DATE - INTERVAL '1 day', 'planned', NULL, NULL, 35.0, 6),
        ('RT-2024-020', '강남 7권역 오후', 2, 10, CURRENT_DATE, 'planned', NULL, NULL, 40.0, 7);
    """)

    # === Route Stops (경로별 정류장) - 확장 (다양한 city 값) ===
    op.execute("""
        INSERT INTO route_stops (route_id, shipment_id, stop_sequence, address, city, postal_code, latitude, longitude, planned_arrival, actual_arrival, status, notes) VALUES
        (1, 1, 1, '서울시 강남구 삼성동 159', '강남', '06288', 37.5085, 127.0632, (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '09:00', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '08:55', 'completed', '첫 번째 배송'),
        (1, NULL, 2, '서울시 강남구 역삼동 823', '강남', '06236', 37.5004, 127.0366, (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '09:30', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '09:25', 'completed', NULL),
        (1, NULL, 3, '서울시 강남구 논현동 63', '강남', '06032', 37.5148, 127.0301, (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '10:05', 'completed', NULL),
        (2, 2, 1, '서울시 강남구 압구정로 165', '강남', '06001', 37.5273, 127.0283, (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '14:00', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '13:50', 'completed', NULL),
        (2, NULL, 2, '서울시 강남구 도산대로 456', '강남', '06040', 37.5230, 127.0380, (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '14:30', (CURRENT_DATE - INTERVAL '84 days')::timestamp + TIME '14:25', 'completed', NULL),
        (3, 3, 1, '서울시 송파구 올림픽로 240', '송파', '05551', 37.5145, 127.1058, (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '10:05', 'completed', NULL),
        (3, NULL, 2, '서울시 송파구 잠실동 40', '송파', '05505', 37.5133, 127.1002, (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '11:00', (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '11:10', 'completed', NULL),
        (3, NULL, 3, '서울시 송파구 문정동 123', '송파', '05836', 37.4852, 127.1229, (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '12:00', (CURRENT_DATE - INTERVAL '74 days')::timestamp + TIME '12:05', 'completed', NULL),
        (4, 4, 1, '서울시 성동구 왕십리로 83', '성동', '04763', 37.5614, 127.0395, (CURRENT_DATE - INTERVAL '69 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '69 days')::timestamp + TIME '10:10', 'completed', NULL),
        (5, 6, 1, '경기도 성남시 분당구 정자일로 95', '분당', '13561', 37.3595, 127.1086, (CURRENT_DATE - INTERVAL '59 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '59 days')::timestamp + TIME '10:05', 'completed', NULL),
        (5, NULL, 2, '경기도 성남시 분당구 서현동 250', '분당', '13590', 37.3834, 127.1231, (CURRENT_DATE - INTERVAL '59 days')::timestamp + TIME '11:00', (CURRENT_DATE - INTERVAL '59 days')::timestamp + TIME '11:10', 'completed', NULL),
        (6, 8, 1, '서울시 서초구 헌릉로 8', '서초', '06796', 37.4832, 127.0042, (CURRENT_DATE - INTERVAL '49 days')::timestamp + TIME '09:00', (CURRENT_DATE - INTERVAL '49 days')::timestamp + TIME '09:05', 'completed', NULL),
        (6, NULL, 2, '서울시 서초구 서초대로 398', '서초', '06620', 37.4919, 127.0074, (CURRENT_DATE - INTERVAL '49 days')::timestamp + TIME '09:30', (CURRENT_DATE - INTERVAL '49 days')::timestamp + TIME '09:35', 'completed', NULL),
        (7, 7, 1, '제주시 첨단로 242', '제주', '63309', 33.4506, 126.5706, (CURRENT_DATE - INTERVAL '54 days')::timestamp + TIME '14:00', (CURRENT_DATE - INTERVAL '54 days')::timestamp + TIME '14:15', 'completed', '도서 지역'),
        (8, 9, 1, '서울시 강남구 논현로 508', '강남', '06141', 37.5090, 127.0234, (CURRENT_DATE - INTERVAL '44 days')::timestamp + TIME '10:30', (CURRENT_DATE - INTERVAL '44 days')::timestamp + TIME '10:25', 'completed', NULL),
        (9, 10, 1, '서울시 강남구 테헤란로 405', '강남', '06168', 37.5060, 127.0580, (CURRENT_DATE - INTERVAL '39 days')::timestamp + TIME '09:00', (CURRENT_DATE - INTERVAL '39 days')::timestamp + TIME '09:10', 'completed', NULL),
        (10, 11, 1, '서울시 강남구 도산대로 123', '강남', '06038', 37.5225, 127.0376, (CURRENT_DATE - INTERVAL '34 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '34 days')::timestamp + TIME '10:05', 'completed', NULL),
        (11, 13, 1, '부산시 해운대구 해운대로 456', '해운대', '48094', 35.1631, 129.1637, (CURRENT_DATE - INTERVAL '27 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '27 days')::timestamp + TIME '10:15', 'completed', NULL),
        (11, NULL, 2, '부산시 해운대구 센텀로 123', '해운대', '48058', 35.1695, 129.1316, (CURRENT_DATE - INTERVAL '27 days')::timestamp + TIME '11:00', NULL, 'pending', NULL),
        (12, 14, 1, '대구시 수성구 범어로 789', '수성', '42019', 35.8577, 128.6294, (CURRENT_DATE - INTERVAL '24 days')::timestamp + TIME '10:00', (CURRENT_DATE - INTERVAL '24 days')::timestamp + TIME '10:20', 'completed', NULL),
        (13, 15, 1, '서울시 강남구 삼성동 159', '강남', '06288', 37.5085, 127.0632, (CURRENT_DATE - INTERVAL '20 days')::timestamp + TIME '09:00', NULL, 'pending', NULL),
        (13, NULL, 2, '서울시 강남구 청담동 87', '강남', '06083', 37.5242, 127.0468, (CURRENT_DATE - INTERVAL '20 days')::timestamp + TIME '10:00', NULL, 'pending', NULL),
        (14, 16, 1, '서울시 송파구 송파대로 570', '송파', '05855', 37.4746, 127.1234, (CURRENT_DATE - INTERVAL '18 days')::timestamp + TIME '09:30', NULL, 'pending', NULL),
        (15, 17, 1, '인천시 남동구 경인로 321', '인천 남동', '21570', 37.4091, 126.7316, (CURRENT_DATE - INTERVAL '15 days')::timestamp + TIME '10:00', NULL, 'pending', NULL),
        (16, 18, 1, '경기도 수원시 팔달구 효원로 147', '수원', '16490', 37.2849, 127.0156, (CURRENT_DATE - INTERVAL '8 days')::timestamp + TIME '09:00', NULL, 'pending', '대량 배송'),
        (16, NULL, 2, '경기도 수원시 영통구 광교로 145', '수원', '16516', 37.2993, 127.0436, (CURRENT_DATE - INTERVAL '8 days')::timestamp + TIME '10:00', NULL, 'pending', NULL);
    """)

    # ============================================================
    # 4. Sales (매출) 데이터 - 50건+ (최근 3개월, CURRENT_DATE 기반)
    # ============================================================
    op.execute("""
        INSERT INTO sales (order_id, product_id, customer_id, sale_date, quantity, unit_price, total_amount, region, channel) VALUES
        -- 3개월 전 (delivered 주문들)
        (1, 1, 1, CURRENT_TIMESTAMP - INTERVAL '85 days', 50, 1200000.00, 60000000.00, '서울', 'offline'),
        (2, 2, 2, CURRENT_TIMESTAMP - INTERVAL '80 days', 30, 800000.00, 24000000.00, '서울', 'offline'),
        (3, 3, 3, CURRENT_TIMESTAMP - INTERVAL '75 days', 10, 1500000.00, 15000000.00, '서울', 'wholesale'),
        (4, 5, 4, CURRENT_TIMESTAMP - INTERVAL '70 days', 500, 12000.00, 6000000.00, '서울', 'wholesale'),
        (4, 6, 4, CURRENT_TIMESTAMP - INTERVAL '70 days', 300, 8500.00, 2550000.00, '서울', 'wholesale'),
        (5, 1, 5, CURRENT_TIMESTAMP - INTERVAL '65 days', 20, 1200000.00, 24000000.00, '서울', 'online'),
        (5, 4, 5, CURRENT_TIMESTAMP - INTERVAL '65 days', 200, 45000.00, 9000000.00, '서울', 'online'),
        (6, 8, 6, CURRENT_TIMESTAMP - INTERVAL '60 days', 200, 59000.00, 11800000.00, '경기', 'wholesale'),
        (7, 8, 7, CURRENT_TIMESTAMP - INTERVAL '55 days', 100, 59000.00, 5900000.00, '제주', 'wholesale'),
        (8, 9, 8, CURRENT_TIMESTAMP - INTERVAL '50 days', 10, 350000.00, 3500000.00, '서울', 'online'),
        -- 2개월 전
        (9, 1, 9, CURRENT_TIMESTAMP - INTERVAL '45 days', 10, 1200000.00, 12000000.00, '서울', 'offline'),
        (9, 22, 9, CURRENT_TIMESTAMP - INTERVAL '45 days', 10, 550000.00, 5500000.00, '서울', 'offline'),
        (10, 3, 10, CURRENT_TIMESTAMP - INTERVAL '40 days', 12, 1500000.00, 18000000.00, '서울', 'wholesale'),
        (10, 4, 10, CURRENT_TIMESTAMP - INTERVAL '40 days', 100, 45000.00, 4500000.00, '서울', 'wholesale'),
        (11, 11, 11, CURRENT_TIMESTAMP - INTERVAL '35 days', 100, 38000.00, 3800000.00, '서울', 'offline'),
        (11, 12, 11, CURRENT_TIMESTAMP - INTERVAL '35 days', 100, 25000.00, 2500000.00, '서울', 'offline'),
        (11, 13, 11, CURRENT_TIMESTAMP - INTERVAL '35 days', 100, 22000.00, 2200000.00, '서울', 'offline'),
        (12, 20, 12, CURRENT_TIMESTAMP - INTERVAL '32 days', 100, 69000.00, 6900000.00, '서울', 'online'),
        (12, 21, 12, CURRENT_TIMESTAMP - INTERVAL '32 days', 150, 55000.00, 8250000.00, '서울', 'online'),
        -- 지난달 (1~30일 전)
        (NULL, 14, 14, CURRENT_TIMESTAMP - INTERVAL '28 days', 80, 35000.00, 2800000.00, '대구', 'offline'),
        (NULL, 15, 14, CURRENT_TIMESTAMP - INTERVAL '28 days', 60, 42000.00, 2520000.00, '대구', 'offline'),
        (NULL, 16, 13, CURRENT_TIMESTAMP - INTERVAL '26 days', 100, 55000.00, 5500000.00, '부산', 'wholesale'),
        (NULL, 11, 11, CURRENT_TIMESTAMP - INTERVAL '25 days', 200, 38000.00, 7600000.00, '서울', 'offline'),
        (NULL, 27, 11, CURRENT_TIMESTAMP - INTERVAL '25 days', 150, 48000.00, 7200000.00, '서울', 'offline'),
        (NULL, 1, 1, CURRENT_TIMESTAMP - INTERVAL '22 days', 30, 1200000.00, 36000000.00, '서울', 'offline'),
        (NULL, 22, 1, CURRENT_TIMESTAMP - INTERVAL '22 days', 20, 450000.00, 9000000.00, '서울', 'offline'),
        (NULL, 3, 5, CURRENT_TIMESTAMP - INTERVAL '20 days', 15, 1500000.00, 22500000.00, '서울', 'online'),
        (NULL, 23, 5, CURRENT_TIMESTAMP - INTERVAL '20 days', 10, 550000.00, 5500000.00, '서울', 'online'),
        (NULL, 17, 15, CURRENT_TIMESTAMP - INTERVAL '18 days', 300, 8900.00, 2670000.00, '인천', 'wholesale'),
        (NULL, 18, 15, CURRENT_TIMESTAMP - INTERVAL '18 days', 200, 12500.00, 2500000.00, '인천', 'wholesale'),
        (NULL, 19, 15, CURRENT_TIMESTAMP - INTERVAL '18 days', 250, 6500.00, 1625000.00, '인천', 'wholesale'),
        (NULL, 7, 16, CURRENT_TIMESTAMP - INTERVAL '15 days', 200, 5500.00, 1100000.00, '광주', 'offline'),
        (NULL, 25, 16, CURRENT_TIMESTAMP - INTERVAL '15 days', 100, 12000.00, 1200000.00, '광주', 'offline'),
        (NULL, 14, 17, CURRENT_TIMESTAMP - INTERVAL '12 days', 60, 35000.00, 2100000.00, '대전', 'offline'),
        (NULL, 16, 17, CURRENT_TIMESTAMP - INTERVAL '12 days', 50, 55000.00, 2750000.00, '대전', 'offline'),
        (NULL, 1, 18, CURRENT_TIMESTAMP - INTERVAL '10 days', 10, 1200000.00, 12000000.00, '경기', 'wholesale'),
        (NULL, 26, 18, CURRENT_TIMESTAMP - INTERVAL '10 days', 20, 290000.00, 5800000.00, '경기', 'wholesale'),
        (NULL, 12, 11, CURRENT_TIMESTAMP - INTERVAL '8 days', 300, 25000.00, 7500000.00, '서울', 'online'),
        (NULL, 13, 11, CURRENT_TIMESTAMP - INTERVAL '8 days', 250, 22000.00, 5500000.00, '서울', 'online'),
        (NULL, 5, 4, CURRENT_TIMESTAMP - INTERVAL '7 days', 400, 12000.00, 4800000.00, '서울', 'wholesale'),
        (NULL, 6, 4, CURRENT_TIMESTAMP - INTERVAL '7 days', 300, 8500.00, 2550000.00, '서울', 'wholesale'),
        (NULL, 24, 4, CURRENT_TIMESTAMP - INTERVAL '7 days', 200, 15000.00, 3000000.00, '서울', 'wholesale'),
        (NULL, 28, 9, CURRENT_TIMESTAMP - INTERVAL '6 days', 100, 39000.00, 3900000.00, '서울', 'offline'),
        (NULL, 20, 6, CURRENT_TIMESTAMP - INTERVAL '5 days', 80, 69000.00, 5520000.00, '경기', 'online'),
        (NULL, 21, 6, CURRENT_TIMESTAMP - INTERVAL '5 days', 100, 55000.00, 5500000.00, '경기', 'online'),
        (NULL, 29, 3, CURRENT_TIMESTAMP - INTERVAL '4 days', 50, 7500.00, 375000.00, '서울', 'offline'),
        (NULL, 17, 19, CURRENT_TIMESTAMP - INTERVAL '3 days', 100, 8900.00, 890000.00, '경기', 'online'),
        (NULL, 19, 19, CURRENT_TIMESTAMP - INTERVAL '3 days', 200, 6500.00, 1300000.00, '경기', 'online'),
        (NULL, 14, 9, CURRENT_TIMESTAMP - INTERVAL '2 days', 80, 35000.00, 2800000.00, '서울', 'offline'),
        (NULL, 28, 9, CURRENT_TIMESTAMP - INTERVAL '2 days', 100, 39000.00, 3900000.00, '서울', 'offline'),
        (NULL, 2, 2, CURRENT_TIMESTAMP - INTERVAL '1 day', 25, 800000.00, 20000000.00, '서울', 'offline'),
        (NULL, 22, 2, CURRENT_TIMESTAMP - INTERVAL '1 day', 15, 450000.00, 6750000.00, '서울', 'offline'),
        (NULL, 30, 20, CURRENT_TIMESTAMP - INTERVAL '1 day', 5, 180000.00, 900000.00, '제주', 'online');
    """)


def downgrade() -> None:
    # sales 데이터 및 테이블 삭제
    op.execute("DELETE FROM table_permissions WHERE table_name = 'sales';")
    op.execute("DROP TABLE IF EXISTS sales CASCADE;")

    # 확장 데이터 삭제
    op.execute("DELETE FROM route_stops;")
    op.execute("DELETE FROM delivery_routes;")
    op.execute("DELETE FROM shipment_items;")
    op.execute("DELETE FROM shipments;")
    op.execute("DELETE FROM vehicles;")
    op.execute("DELETE FROM carriers;")
    op.execute("DELETE FROM order_items;")
    op.execute("DELETE FROM orders;")
    op.execute("DELETE FROM customers;")
    op.execute("DELETE FROM inventory_transactions;")
    op.execute("DELETE FROM inventory;")
    op.execute("DELETE FROM products;")
    op.execute("DELETE FROM product_categories;")
    op.execute("DELETE FROM warehouse_zones;")
    op.execute("DELETE FROM warehouses;")
    op.execute("DELETE FROM drivers;")

    # ID 시퀀스 리셋
    for table in [
        "drivers", "warehouses", "warehouse_zones", "product_categories",
        "products", "inventory", "inventory_transactions", "customers",
        "orders", "order_items", "carriers", "vehicles", "shipments",
        "shipment_items", "delivery_routes", "route_stops",
    ]:
        op.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;")

    # 003의 원래 데이터 복원은 003 migration이 담당
    # downgrade 004 → 003 후, 003의 upgrade를 다시 실행하면 원래 데이터 복원
