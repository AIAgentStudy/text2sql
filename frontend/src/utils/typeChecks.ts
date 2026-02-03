/**
 * 값이 숫자로 변환 가능한지 확인합니다.
 * typeof가 'number'이거나, 빈 문자열이 아닌 문자열이 Number()로 유한한 숫자가 되는 경우 true.
 */
export function isNumericValue(value: unknown): boolean {
  if (typeof value === 'number') return true;
  if (typeof value === 'string' && value.trim() !== '') {
    return isFinite(Number(value));
  }
  return false;
}

/**
 * 값을 숫자로 변환합니다. 변환 불가 시 NaN 반환.
 */
export function toNumber(value: unknown): number {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') return Number(value);
  return NaN;
}
