/** Normalize backend booking status (lowercase enum) for UI comparisons */
export function normalizeBookingStatus(status: string | undefined | null): string {
  if (!status) return '';
  return String(status).toLowerCase().replace(/-/g, '_');
}

export function formatServiceAddress(
  serviceAddress: Record<string, unknown> | string | null | undefined
): string {
  if (!serviceAddress) return 'Address not provided';
  if (typeof serviceAddress === 'string') return serviceAddress;
  if (typeof serviceAddress.full_address === 'string') return serviceAddress.full_address;
  const parts = [serviceAddress.address, serviceAddress.city, serviceAddress.pincode].filter(Boolean);
  return parts.length > 0 ? parts.join(', ') : 'Address not provided';
}

export type BookingListItem = {
  id: string;
  service_category: string;
  status: string;
  preferred_date: string;
  estimated_price?: number;
  service_address?: Record<string, unknown> | string;
  address?: string;
  service_description?: string;
  problem_description?: string;
};

export function mapBookingItem(raw: Record<string, unknown>): BookingListItem {
  const serviceAddress = raw.service_address as Record<string, unknown> | string | undefined;
  return {
    id: String(raw.id),
    service_category: String(raw.service_category ?? ''),
    status: String(raw.status ?? ''),
    preferred_date: String(raw.preferred_date ?? ''),
    estimated_price: typeof raw.estimated_price === 'number' ? raw.estimated_price : undefined,
    service_address: serviceAddress,
    address:
      typeof raw.address === 'string'
        ? raw.address
        : formatServiceAddress(serviceAddress),
    service_description:
      typeof raw.service_description === 'string' ? raw.service_description : undefined,
    problem_description:
      typeof raw.problem_description === 'string'
        ? raw.problem_description
        : typeof raw.service_description === 'string'
          ? raw.service_description
          : undefined,
  };
}

export function extractListItems<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (obj.data && typeof obj.data === 'object') {
      const nested = obj.data as Record<string, unknown>;
      if (Array.isArray(nested.items)) return nested.items as T[];
    }
  }
  return [];
}
