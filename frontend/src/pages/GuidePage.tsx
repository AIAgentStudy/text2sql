/**
 * 이용가이드 페이지
 *
 * Text2SQL Agent 시스템의 사용법, 데이터베이스 구조, 질문 예시를 안내합니다.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

interface CollapsibleProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function Collapsible({ title, children, defaultOpen = false }: CollapsibleProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-3 flex items-center justify-between text-left bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <span className="text-sm font-medium text-gray-900">{title}</span>
        <span className="text-gray-400 text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && <div className="px-4 py-3 text-sm text-gray-600">{children}</div>}
    </div>
  );
}

function TableDef({ name, desc, columns }: { name: string; desc: string; columns: string[] }) {
  return (
    <div className="mb-3 last:mb-0">
      <p className="font-mono text-purple-600 text-xs">{name}</p>
      <p className="text-xs text-gray-500 mb-1">{desc}</p>
      <p className="text-xs text-gray-400 leading-relaxed">{columns.join(' · ')}</p>
    </div>
  );
}

export function GuidePage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="h-screen bg-gradient-dark flex flex-col overflow-hidden">
      {/* 헤더 - ChatPage와 동일한 glass 스타일 */}
      <header className="glass border-b border-surface-border relative flex-shrink-0">
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary-500/50 to-transparent"></div>
        <div className="px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gradient">이용가이드</h1>
            <p className="text-sm text-content-secondary">Text2SQL Agent 사용 안내</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-content-primary">{user?.name}</p>
              <p className="text-xs text-content-tertiary">{user?.roles.join(', ')}</p>
            </div>
            <button
              onClick={() => navigate('/')}
              className="px-3 py-1.5 text-sm text-content-secondary hover:text-content-primary hover:bg-surface-hover rounded-lg transition-all duration-200"
            >
              채팅으로 돌아가기
            </button>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 text-sm text-content-secondary hover:text-content-primary hover:bg-surface-hover rounded-lg transition-all duration-200"
            >
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto bg-white">
        <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">

          {/* 1. 시스템 소개 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">시스템 소개</h2>
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 text-sm text-gray-600 leading-relaxed space-y-2">
              <p>
                <strong className="text-gray-900">Text2SQL Agent</strong>는 자연어 질문을 SQL로 자동 변환하여
                데이터베이스에서 결과를 조회하는 AI 에이전트입니다.
              </p>
              <p>
                한국어로 질문하면 LLM이 SQL 쿼리를 생성하고, 3단계 검증(키워드·스키마·시맨틱)을 거쳐
                안전하게 실행합니다. SELECT 쿼리만 허용되며, 데이터 변경은 불가합니다.
              </p>
              <p>
                결과는 테이블과 차트(막대·선·파이)로 자동 시각화되며,
                대화 맥락을 유지하여 후속 질문도 가능합니다.
              </p>
            </div>
          </section>

          {/* 2. 비즈니스 도메인 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">비즈니스 도메인</h2>
            <p className="text-sm text-gray-600 mb-4">
              이커머스 물류 관리 시스템의 데이터를 기반으로 합니다.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                { label: '창고', value: '10개', desc: '전국 물류센터' },
                { label: '상품', value: '30개', desc: '5개 카테고리' },
                { label: '고객사', value: '20개', desc: 'B2B 거래처' },
                { label: '운송사', value: '10개', desc: '배송 파트너' },
                { label: '배송기사', value: '10명', desc: '현장 인력' },
                { label: '주문/배송/매출', value: '다수', desc: '일별 트랜잭션' },
              ].map((item) => (
                <div key={item.label} className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4 text-center">
                  <p className="text-2xl font-bold text-purple-600">{item.value}</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">{item.label}</p>
                  <p className="text-xs text-gray-500">{item.desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* 3. 데이터베이스 구조 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">데이터베이스 구조</h2>
            <p className="text-sm text-gray-600 mb-4">
              총 21개 테이블이 5개 도메인으로 구성됩니다. 접근 가능한 테이블은 역할에 따라 다릅니다.
            </p>
            <div className="space-y-2">
              <Collapsible title="인증/권한 (5 tables)">
                <TableDef
                  name="users"
                  desc="사용자 계정 정보"
                  columns={['id', 'username', 'name', 'email', 'is_active', 'created_at']}
                />
                <TableDef
                  name="roles"
                  desc="역할 정의 (admin, manager, viewer)"
                  columns={['id', 'name', 'description']}
                />
                <TableDef
                  name="user_roles"
                  desc="사용자-역할 매핑"
                  columns={['user_id', 'role_id']}
                />
                <TableDef
                  name="table_permissions"
                  desc="역할별 테이블 접근 권한"
                  columns={['role_id', 'table_name', 'can_read']}
                />
                <TableDef
                  name="drivers"
                  desc="배송기사 상세 정보 (admin 전용)"
                  columns={['id', 'name', 'phone', 'license_number', 'vehicle_type', 'status']}
                />
              </Collapsible>

              <Collapsible title="창고/재고 (5 tables)">
                <TableDef
                  name="warehouses"
                  desc="물류 창고"
                  columns={['id', 'name', 'code', 'address', 'region', 'capacity_sqm', 'is_active']}
                />
                <TableDef
                  name="warehouse_zones"
                  desc="창고 내 구역"
                  columns={['id', 'warehouse_id', 'name', 'zone_type', 'capacity']}
                />
                <TableDef
                  name="products"
                  desc="상품 마스터"
                  columns={['id', 'name', 'sku', 'category_id', 'price', 'weight_kg']}
                />
                <TableDef
                  name="product_categories"
                  desc="상품 카테고리"
                  columns={['id', 'name', 'description']}
                />
                <TableDef
                  name="inventory"
                  desc="재고 현황"
                  columns={['id', 'warehouse_id', 'product_id', 'zone_id', 'quantity', 'last_updated']}
                />
              </Collapsible>

              <Collapsible title="주문관리 (3 tables)">
                <TableDef
                  name="customers"
                  desc="B2B 고객사"
                  columns={['id', 'name', 'business_number', 'contact_name', 'contact_phone', 'region']}
                />
                <TableDef
                  name="orders"
                  desc="주문 헤더"
                  columns={['id', 'customer_id', 'order_date', 'status', 'total_amount', 'warehouse_id']}
                />
                <TableDef
                  name="order_items"
                  desc="주문 상세 품목"
                  columns={['id', 'order_id', 'product_id', 'quantity', 'unit_price', 'subtotal']}
                />
              </Collapsible>

              <Collapsible title="배송/물류 (6 tables)">
                <TableDef
                  name="carriers"
                  desc="운송사"
                  columns={['id', 'name', 'contact_phone', 'service_regions', 'is_active']}
                />
                <TableDef
                  name="vehicles"
                  desc="배송 차량"
                  columns={['id', 'carrier_id', 'plate_number', 'vehicle_type', 'capacity_kg']}
                />
                <TableDef
                  name="shipments"
                  desc="배송 건"
                  columns={['id', 'order_id', 'carrier_id', 'driver_id', 'status', 'shipped_at', 'delivered_at']}
                />
                <TableDef
                  name="shipment_items"
                  desc="배송 품목"
                  columns={['id', 'shipment_id', 'order_item_id', 'quantity']}
                />
                <TableDef
                  name="delivery_routes"
                  desc="배송 경로"
                  columns={['id', 'shipment_id', 'vehicle_id', 'route_date', 'status']}
                />
                <TableDef
                  name="route_stops"
                  desc="경로 정류장"
                  columns={['id', 'route_id', 'stop_order', 'address', 'arrived_at']}
                />
              </Collapsible>

              <Collapsible title="거래/분석 (2 tables)">
                <TableDef
                  name="inventory_transactions"
                  desc="재고 입출고 이력"
                  columns={['id', 'inventory_id', 'transaction_type', 'quantity', 'reference_id', 'created_at']}
                />
                <TableDef
                  name="sales"
                  desc="매출 집계"
                  columns={['id', 'order_id', 'product_id', 'sale_date', 'quantity', 'unit_price', 'total_amount', 'region']}
                />
              </Collapsible>
            </div>
          </section>

          {/* 4. 질문 예시 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">질문 예시</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { category: '매출 분석', query: '이번 달 지역별 매출 합계를 알려줘' },
                { category: '고객 분석', query: '주문 금액이 가장 높은 고객사 5곳은?' },
                { category: '주문 추이', query: '최근 3개월간 월별 주문 건수 추이를 보여줘' },
                { category: '재고 현황', query: '재고 수량이 10개 이하인 상품 목록' },
                { category: '배송 성과', query: '운송사별 평균 배송 소요시간은?' },
                { category: '상품 순위', query: '가장 많이 팔린 상품 TOP 10' },
              ].map((item) => (
                <div key={item.category} className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                  <p className="text-xs font-medium text-purple-600 mb-1">{item.category}</p>
                  <p className="text-sm text-gray-900">&ldquo;{item.query}&rdquo;</p>
                </div>
              ))}
            </div>
          </section>

          {/* 5. 역할별 접근 권한 */}
          <section>
            <h2 className="text-lg font-bold text-gray-900 mb-3">역할별 접근 권한</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                <p className="text-sm font-bold text-red-600 mb-2">Admin</p>
                <p className="text-xs text-gray-600 mb-2">모든 테이블 접근 가능</p>
                <p className="text-xs text-gray-500">
                  인증/권한 테이블 포함 전체 21개 테이블에 접근할 수 있습니다.
                  기사 개인정보 등 민감 데이터도 조회 가능합니다.
                </p>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                <p className="text-sm font-bold text-blue-600 mb-2">Manager</p>
                <p className="text-xs text-gray-600 mb-2">물류 운영 테이블 접근 가능</p>
                <p className="text-xs text-gray-500">
                  창고, 상품, 주문, 배송, 매출 등 15개 테이블에 접근할 수 있습니다.
                  인증/권한 관련 테이블은 제외됩니다.
                </p>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-4">
                <p className="text-sm font-bold text-green-600 mb-2">Viewer</p>
                <p className="text-xs text-gray-600 mb-2">조회 전용 (5개 테이블)</p>
                <p className="text-xs text-gray-500">
                  창고, 상품, 카테고리, 재고, 재고이력 테이블만 조회 가능합니다.
                  주문·배송·매출 데이터는 접근할 수 없습니다.
                </p>
              </div>
            </div>
          </section>

          {/* 6. 사용 팁 */}
          <section className="pb-8">
            <h2 className="text-lg font-bold text-gray-900 mb-3">사용 팁</h2>
            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 space-y-3 text-sm text-gray-600">
              <div>
                <p className="font-medium text-gray-900">1. 구체적으로 질문하세요</p>
                <p className="text-xs text-gray-500 mt-1">
                  &ldquo;매출 보여줘&rdquo; 보다 &ldquo;2024년 1월 서울 지역 매출 합계&rdquo;처럼
                  기간, 지역, 조건을 명시하면 정확한 결과를 얻을 수 있습니다.
                </p>
              </div>
              <div>
                <p className="font-medium text-gray-900">2. 후속 질문을 활용하세요</p>
                <p className="text-xs text-gray-500 mt-1">
                  이전 대화 맥락이 유지되므로 &ldquo;그 중 상위 5개만&rdquo;,
                  &ldquo;같은 기간 경기도는?&rdquo; 같은 후속 질문이 가능합니다.
                </p>
              </div>
              <div>
                <p className="font-medium text-gray-900">3. 쿼리 확인 후 실행하세요</p>
                <p className="text-xs text-gray-500 mt-1">
                  생성된 SQL 쿼리가 표시되면 확인 후 실행됩니다.
                  의도와 다른 쿼리는 거부하고 질문을 수정할 수 있습니다.
                </p>
              </div>
              <div>
                <p className="font-medium text-gray-900">4. 제한사항을 참고하세요</p>
                <p className="text-xs text-gray-500 mt-1">
                  쿼리 실행 제한시간 30초, 결과 최대 10,000행, 세션 유지 30분.
                  SELECT 쿼리만 허용되며, 데이터 수정/삭제는 차단됩니다.
                </p>
              </div>
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}
