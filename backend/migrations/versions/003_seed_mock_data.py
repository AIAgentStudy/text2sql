"""Seed mock data

Revision ID: 003
Revises: 002
Create Date: 2024-01-15

테이블당 10개의 Mock 데이터 생성
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === 테스트 계정 생성 ===
    # password: admin123 (bcrypt hash - generated with passlib)
    op.execute("""
        INSERT INTO users (email, password_hash, name, is_active) VALUES
        ('admin@test.com', '$2b$12$H798K22vn2gtOFqdkhIC0OcRim9uwJyBTUM50op4FlzJFejDCvyPK', 'Test Admin', TRUE),
        ('manager@test.com', '$2b$12$H798K22vn2gtOFqdkhIC0OcRim9uwJyBTUM50op4FlzJFejDCvyPK', 'Test Manager', TRUE),
        ('viewer@test.com', '$2b$12$H798K22vn2gtOFqdkhIC0OcRim9uwJyBTUM50op4FlzJFejDCvyPK', 'Test Viewer', TRUE)
    """)
    # 테스트 계정 역할 할당
    op.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id FROM users u, roles r WHERE u.email = 'admin@test.com' AND r.name = 'admin'
    """)
    op.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id FROM users u, roles r WHERE u.email = 'manager@test.com' AND r.name = 'manager'
    """)
    op.execute("""
        INSERT INTO user_roles (user_id, role_id)
        SELECT u.id, r.id FROM users u, roles r WHERE u.email = 'viewer@test.com' AND r.name = 'viewer'
    """)

    # === Drivers (기사 정보) ===
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

    # === Warehouses (창고) ===
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

    # === Warehouse Zones (창고 구역) ===
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

    # === Product Categories (제품 카테고리) ===
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
        ('FURN-OFF', '사무가구', 4, '사무용 가구');
    """)

    # === Products (제품) ===
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
        ('SKU-OFF-002', '책상 D500', 10, '1400mm 사무용 책상', 'EA', 35.000, 140.00, 70.00, 75.00, 250000.00, TRUE);
    """)

    # === Inventory (재고) ===
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
        (10, 4, 8, 80, 8, 'LOT-2024-010', NULL);
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
        (8, 'IN', 400, 'PURCHASE', 1007, '의류 입고');
    """)

    # === Customers (고객) ===
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
        ('CUST-010', 'BGF리테일', '임BGF', 'bgf@example.com', '02-0123-4567', '서울시 강남구 테헤란로 405', '서울', '서울특별시', '06168', 'wholesale', 180000000.00, TRUE);
    """)

    # === Orders (주문) ===
    op.execute("""
        INSERT INTO orders (order_number, customer_id, order_date, status, total_amount, shipping_address, shipping_city, shipping_region, shipping_postal_code, notes) VALUES
        ('ORD-2024-00001', 1, '2024-01-15 09:30:00+09', 'delivered', 60000000.00, '서울시 강남구 삼성동 159', '서울', '서울특별시', '06288', '긴급 배송 요청'),
        ('ORD-2024-00002', 2, '2024-01-16 10:15:00+09', 'delivered', 24000000.00, '서울시 강남구 압구정로 165', '서울', '서울특별시', '06001', NULL),
        ('ORD-2024-00003', 3, '2024-01-17 14:00:00+09', 'shipped', 15000000.00, '서울시 송파구 올림픽로 240', '서울', '서울특별시', '05551', '2층 하역장 도착'),
        ('ORD-2024-00004', 4, '2024-01-18 11:30:00+09', 'processing', 8500000.00, '서울시 성동구 왕십리로 83', '서울', '서울특별시', '04763', NULL),
        ('ORD-2024-00005', 5, '2024-01-19 08:45:00+09', 'confirmed', 30000000.00, '서울시 송파구 송파대로 570', '서울', '서울특별시', '05855', '대량 주문'),
        ('ORD-2024-00006', 6, '2024-01-20 13:20:00+09', 'pending', 12000000.00, '경기도 성남시 분당구 정자일로 95', '성남', '경기도', '13561', NULL),
        ('ORD-2024-00007', 7, '2024-01-21 15:45:00+09', 'pending', 5900000.00, '제주시 첨단로 242', '제주', '제주특별자치도', '63309', '도서 지역 배송'),
        ('ORD-2024-00008', 8, '2024-01-22 09:00:00+09', 'cancelled', 3500000.00, '서울시 서초구 헌릉로 8', '서울', '서울특별시', '06796', '고객 요청 취소'),
        ('ORD-2024-00009', 9, '2024-01-23 10:30:00+09', 'confirmed', 17500000.00, '서울시 강남구 논현로 508', '서울', '서울특별시', '06141', NULL),
        ('ORD-2024-00010', 10, '2024-01-24 14:15:00+09', 'confirmed', 22000000.00, '서울시 강남구 테헤란로 405', '서울', '서울특별시', '06168', NULL);
    """)

    # === Order Items (주문 상세) ===
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
        (8, 9, 10, 350000.00, 0, 3500000.00);
    """)

    # === Carriers (운송사) ===
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

    # === Vehicles (차량) ===
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

    # === Shipments (배송) ===
    op.execute("""
        INSERT INTO shipments (shipment_number, order_id, carrier_id, vehicle_id, driver_id, status, origin_warehouse_id, destination_address, destination_city, destination_region, destination_postal_code, estimated_delivery, actual_delivery, shipping_cost, tracking_number, notes) VALUES
        ('SHP-2024-00001', 1, 1, 1, 1, 'delivered', 1, '서울시 강남구 삼성동 159', '서울', '서울특별시', '06288', '2024-01-16 14:00:00+09', '2024-01-16 13:30:00+09', 50000.00, 'CJ1234567890', '정시 배송 완료'),
        ('SHP-2024-00002', 2, 2, 3, 2, 'delivered', 2, '서울시 강남구 압구정로 165', '서울', '서울특별시', '06001', '2024-01-17 16:00:00+09', '2024-01-17 15:45:00+09', 40000.00, 'LT2345678901', NULL),
        ('SHP-2024-00003', 3, 1, 2, 3, 'in_transit', 1, '서울시 송파구 올림픽로 240', '서울', '서울특별시', '05551', '2024-01-18 12:00:00+09', NULL, 45000.00, 'CJ3456789012', '배송 중'),
        ('SHP-2024-00004', 4, 3, 5, 4, 'picked_up', 3, '서울시 성동구 왕십리로 83', '서울', '서울특별시', '04763', '2024-01-19 17:00:00+09', NULL, 35000.00, 'HJ4567890123', NULL),
        ('SHP-2024-00005', 5, 6, 8, 5, 'pending', 1, '서울시 송파구 송파대로 570', '서울', '서울특별시', '05855', '2024-01-20 10:00:00+09', NULL, 30000.00, NULL, '로켓배송'),
        ('SHP-2024-00006', 6, 4, 6, 6, 'pending', 4, '경기도 성남시 분당구 정자일로 95', '성남', '경기도', '13561', '2024-01-21 14:00:00+09', NULL, 25000.00, NULL, NULL),
        ('SHP-2024-00007', 7, 5, 7, 7, 'pending', 10, '제주시 첨단로 242', '제주', '제주특별자치도', '63309', '2024-01-23 18:00:00+09', NULL, 80000.00, NULL, '항공 운송'),
        ('SHP-2024-00008', 9, 1, 1, 8, 'pending', 2, '서울시 강남구 논현로 508', '서울', '서울특별시', '06141', '2024-01-24 11:00:00+09', NULL, 35000.00, NULL, NULL),
        ('SHP-2024-00009', 10, 2, 4, 9, 'pending', 1, '서울시 강남구 테헤란로 405', '서울', '서울특별시', '06168', '2024-01-25 15:00:00+09', NULL, 40000.00, NULL, NULL),
        ('SHP-2024-00010', 1, 1, 2, 10, 'delivered', 1, '서울시 강남구 삼성동 159-1', '서울', '서울특별시', '06288', '2024-01-16 16:00:00+09', '2024-01-16 15:50:00+09', 25000.00, 'CJ5678901234', '추가 배송분');
    """)

    # === Shipment Items (배송 상세) ===
    op.execute("""
        INSERT INTO shipment_items (shipment_id, product_id, quantity, picked_quantity) VALUES
        (1, 1, 50, 50),
        (2, 2, 30, 30),
        (3, 3, 10, 10),
        (4, 5, 500, 300),
        (4, 6, 300, 200),
        (5, 1, 20, 0),
        (5, 4, 200, 0),
        (6, 8, 200, 0),
        (7, 8, 100, 0),
        (8, 9, 5, 0);
    """)

    # === Delivery Routes (배송 경로) ===
    op.execute("""
        INSERT INTO delivery_routes (route_code, name, vehicle_id, driver_id, route_date, status, start_time, end_time, total_distance_km, total_stops) VALUES
        ('RT-2024-001', '강남 1권역 오전', 1, 1, '2024-01-16', 'completed', '2024-01-16 08:00:00+09', '2024-01-16 14:00:00+09', 45.5, 8),
        ('RT-2024-002', '강남 2권역 오후', 2, 2, '2024-01-16', 'completed', '2024-01-16 13:00:00+09', '2024-01-16 18:30:00+09', 38.2, 6),
        ('RT-2024-003', '송파 1권역', 3, 3, '2024-01-17', 'in_progress', '2024-01-17 09:00:00+09', NULL, 52.0, 10),
        ('RT-2024-004', '성동 권역', 5, 4, '2024-01-18', 'planned', NULL, NULL, 35.0, 7),
        ('RT-2024-005', '분당 권역', 6, 5, '2024-01-19', 'planned', NULL, NULL, 48.5, 9),
        ('RT-2024-006', '서초 1권역', 8, 6, '2024-01-20', 'planned', NULL, NULL, 30.0, 5),
        ('RT-2024-007', '제주 권역', 7, 7, '2024-01-22', 'planned', NULL, NULL, 65.0, 4),
        ('RT-2024-008', '강남 3권역', 1, 8, '2024-01-23', 'planned', NULL, NULL, 40.0, 7),
        ('RT-2024-009', '강남 4권역', 4, 9, '2024-01-24', 'planned', NULL, NULL, 42.5, 8),
        ('RT-2024-010', '강남 5권역', 2, 10, '2024-01-25', 'planned', NULL, NULL, 38.0, 6);
    """)

    # === Route Stops (경로별 정류장) ===
    op.execute("""
        INSERT INTO route_stops (route_id, shipment_id, stop_sequence, address, city, postal_code, latitude, longitude, planned_arrival, actual_arrival, status, notes) VALUES
        (1, 1, 1, '서울시 강남구 삼성동 159', '서울', '06288', 37.5085, 127.0632, '2024-01-16 09:00:00+09', '2024-01-16 08:55:00+09', 'completed', '첫 번째 배송'),
        (1, 10, 2, '서울시 강남구 삼성동 159-1', '서울', '06288', 37.5087, 127.0635, '2024-01-16 09:30:00+09', '2024-01-16 09:25:00+09', 'completed', '추가 배송'),
        (2, 2, 1, '서울시 강남구 압구정로 165', '서울', '06001', 37.5273, 127.0283, '2024-01-16 14:00:00+09', '2024-01-16 13:50:00+09', 'completed', NULL),
        (3, 3, 1, '서울시 송파구 올림픽로 240', '서울', '05551', 37.5145, 127.1058, '2024-01-17 10:00:00+09', '2024-01-17 10:05:00+09', 'completed', NULL),
        (3, NULL, 2, '서울시 송파구 잠실동 40', '서울', '05505', 37.5133, 127.1002, '2024-01-17 11:00:00+09', NULL, 'pending', '추가 픽업'),
        (4, 4, 1, '서울시 성동구 왕십리로 83', '서울', '04763', 37.5614, 127.0395, '2024-01-18 10:00:00+09', NULL, 'pending', NULL),
        (5, 5, 1, '서울시 송파구 송파대로 570', '서울', '05855', 37.4746, 127.1234, '2024-01-19 09:30:00+09', NULL, 'pending', '대량 배송'),
        (6, 6, 1, '경기도 성남시 분당구 정자일로 95', '성남', '13561', 37.3595, 127.1086, '2024-01-20 11:00:00+09', NULL, 'pending', NULL),
        (7, 7, 1, '제주시 첨단로 242', '제주', '63309', 33.4506, 126.5706, '2024-01-22 14:00:00+09', NULL, 'pending', '도서 지역'),
        (8, 8, 1, '서울시 강남구 논현로 508', '서울', '06141', 37.5090, 127.0234, '2024-01-23 10:30:00+09', NULL, 'pending', NULL);
    """)


def downgrade() -> None:
    # 데이터만 삭제 (테이블 구조는 유지)
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
    op.execute("DELETE FROM user_roles;")
    op.execute("DELETE FROM users;")
