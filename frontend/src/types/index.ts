export interface ServiceCategory {
  id: string;
  slug: string;
  name: string;
  description: string;
  icon: string;
  base_price: number;
  skills: string[];
}

export interface Booking {
  id: string;
  service_category: string;
  status: string;
  preferred_date: string;
  estimated_price: number;
  requested_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next?: boolean;
  has_prev?: boolean;
}
