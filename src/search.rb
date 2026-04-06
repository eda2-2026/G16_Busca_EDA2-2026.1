# search.rb
require 'json'
require 'set'

BLOCK_SIZE = 10


class HashTable
  BUCKET_COUNT = 1024

  def initialize
    @buckets = Array.new(BUCKET_COUNT) { [] }
  end


  def hash_fn(key)
    h = 5381
    key.each_char { |c| h = ((h << 5) + h) ^ c.ord }
    (h & 0xFFFFFFFF) % BUCKET_COUNT
  end

  def []=(key, value)
    idx  = hash_fn(key)
    pair = @buckets[idx].find { |k, _| k == key }
    if pair
      pair[1] = value
    else
      @buckets[idx] << [key, value]
    end
  end

  def [](key)
    idx  = hash_fn(key)
    pair = @buckets[idx].find { |k, _| k == key }
    pair ? pair[1] : nil
  end

  def each_pair
    @buckets.each do |bucket|
      bucket.each { |k, v| yield k, v }
    end
  end
end

Product = Struct.new(:id, :name, :price, :image_url)

input      = JSON.parse($stdin.read)
price_min  = input["price_min"].to_f
price_max  = input["price_max"].to_f
query_name = input["query_name"]&.to_s&.downcase&.strip

# Carrega o catálogo
catalog = input["products"].map do |p|
  Product.new(p["id"], p["name"], p["price"].to_f, p["image_url"])
end.sort_by(&:price)

#  Índice Invertido 
inverted_index = HashTable.new

catalog.each do |product|
  tokens = product.name.downcase.scan(/\w+/)
  tokens.each do |token|
    list = inverted_index[token]
    if list.nil?
      inverted_index[token] = [product.id]
    else
      list << product.id
    end
  end
end

valid_ids = nil
if query_name && !query_name.empty?
  query_tokens = query_name.scan(/\w+/)
  if query_tokens.any?
    valid_ids = query_tokens.map do |token|
      matching_ids = []
      inverted_index.each_pair do |key, ids|
        matching_ids |= ids if key.include?(token)
      end
      matching_ids
    end.reduce(:&) || []
  end
end

#  Construção da Busca Indexada
index_1 = catalog.each_with_index.select { |_, i| i % BLOCK_SIZE == 0 }.map { |_, i| i }
index_2 = index_1.each_with_index.select { |_, i| i % BLOCK_SIZE == 0 }.map { |_, i| i }

def bin_lower(index_1, catalog, start, stop, target)
  lo, hi = start, stop
  while lo <= hi
    mid = (lo + hi) / 2
    catalog[index_1[mid]].price < target ? lo = mid + 1 : hi = mid - 1
  end
  lo
end

def bin_upper(index_1, catalog, start, stop, target)
  lo, hi = start, stop
  while lo <= hi
    mid = (lo + hi) / 2
    catalog[index_1[mid]].price <= target ? lo = mid + 1 : hi = mid - 1
  end
  lo - 1
end

def search_range(catalog, index_1, index_2, price_min, price_max)
  lo, hi = 0, index_2.size - 1
  while lo <= hi
    mid = (lo + hi) / 2
    catalog[index_1[index_2[mid]]].price < price_min ? lo = mid + 1 : hi = mid - 1
  end
  idx2_lo = lo

  lo, hi = 0, index_2.size - 1
  while lo <= hi
    mid = (lo + hi) / 2
    catalog[index_1[index_2[mid]]].price <= price_max ? lo = mid + 1 : hi = mid - 1
  end
  idx2_hi = lo - 1

  i1_start = [[idx2_lo - 1, 0].max * BLOCK_SIZE, 0].max
  i1_end   = [[idx2_hi + 1, index_2.size - 1].min * BLOCK_SIZE + BLOCK_SIZE - 1, index_1.size - 1].min

  i1_lo = bin_lower(index_1, catalog, i1_start, i1_end, price_min)
  i1_hi = bin_upper(index_1, catalog, i1_start, i1_end, price_max)

  seq_start = [[i1_lo - 1, 0].max * BLOCK_SIZE, 0].max
  seq_end   = [[i1_hi + 1, index_1.size - 1].min * BLOCK_SIZE + BLOCK_SIZE - 1, catalog.size - 1].min

  catalog[seq_start..seq_end].select { |p| p.price >= price_min && p.price <= price_max }
end

#  Cruzamento de dados
results = search_range(catalog, index_1, index_2, price_min, price_max)

if valid_ids
  valid_ids_set = valid_ids.to_set
  results.select! { |p| valid_ids_set.include?(p.id) }
end

# 5. Saída JSON formatada para o Flask
output = results.map do |p|
  { id: p.id, name: p.name, price: p.price, image_url: p.image_url }
end

puts output.to_json
