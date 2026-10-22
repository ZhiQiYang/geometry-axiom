# frozen_string_literal: true

# 標準 ZIP/Deflate；只封裝載入器與執行期檔案，不需要安裝 gem。
require 'zlib'
require 'fileutils'
require 'digest'

root = File.expand_path(__dir__)
files = ['geometry_framing.rb'] + Dir.chdir(root) do
  Dir['geometry_framing/**/*'].select { |p| File.file?(p) && %w[.rb .html .css .js].include?(File.extname(p)) }.sort
end
abort '找不到插件載入器' unless File.file?(File.join(root, files.first))
output = File.join(root, 'releases', 'geometry-framing-0.1.0.rbz')
FileUtils.mkdir_p(File.dirname(output))
central = ''.b
offset = 0
date = ((2026 - 1980) << 9) | (10 << 5) | 13
File.open(output, 'wb') do |zip|
  files.each do |path|
    name = path.encode(Encoding::UTF_8).b
    data = File.binread(File.join(root, path))
    stream = Zlib::Deflate.new(Zlib::BEST_COMPRESSION, -Zlib::MAX_WBITS)
    compressed = stream.deflate(data, Zlib::FINISH)
    stream.close
    crc = Zlib.crc32(data)
    flags = 0x0800 # UTF-8 檔名
    local = [0x04034b50, 20, flags, 8, 0, date, crc, compressed.bytesize, data.bytesize, name.bytesize, 0].pack('VvvvvvVVVvv')
    zip.write(local + name + compressed)
    central << [0x02014b50, 20, 20, flags, 8, 0, date, crc, compressed.bytesize, data.bytesize,
                name.bytesize, 0, 0, 0, 0, 0, offset].pack('VvvvvvvVVVvvvvvVV') << name
    offset += local.bytesize + name.bytesize + compressed.bytesize
  end
  zip.write(central)
  zip.write([0x06054b50, 0, 0, files.length, files.length, central.bytesize, offset, 0].pack('VvvvvVVv'))
end
puts "已打包 #{output}"
puts "#{files.length} 個執行期檔案；#{File.size(output)} bytes"
puts "SHA256 #{Digest::SHA256.file(output).hexdigest}"
