# frozen_string_literal: true

# ruby sketchup-plugin/test/run_mutations.rb
# 真正移除隔離複本中的規則，驗證對應 minitest 會失敗；正式程式沒有突變開關。
require 'digest'
require 'fileutils'
require 'open3'
require 'rbconfig'
require 'tmpdir'

ROOT = File.expand_path('..', __dir__)
SEED = '20261013'
MUTATIONS = [
  { id: 'edge_shift', rule: '收邊挪縫', file: 'panel_axis.rb',
    before: 'if !seams.empty? && seams.last > limit + 1e-9', after: 'if false', test: 'test_edge_shift_rule' },
  { id: 'column_edge', rule: '柱邊料', file: 'flat_ceiling.rb',
    before: 'next if ri.positive? && !p[:colEdge]', after: 'next if ri.positive?', test: 'test_column_edge_rule' },
  { id: 'primary_continuity', rule: '主支不可斷開', file: 'checks.rb',
    before: 'continuity_ok = g[:clashes].empty?', after: 'continuity_ok = true', test: 'test_primary_continuity_rule' }
].freeze

def run(command)
  puts "命令：#{command.map { |item| item.include?(' ') ? item.inspect : item }.join(' ')}"
  output, status = Open3.capture2e(*command)
  output = output.force_encoding(Encoding::UTF_8)
  print output
  puts "exit_code=#{status.exitstatus.inspect}"
  [output, status.exitstatus]
end

puts "Ruby：#{RUBY_DESCRIPTION}"
puts '基準線：先確認未改規則的完整 minitest 全過'
_output, baseline = run([RbConfig.ruby, File.join(__dir__, 'run.rb'), '--seed', SEED])
unless baseline.zero?
  warn '基準線失敗；不把環境問題或既有失敗算成突變被偵測。'
  exit 2
end

originals = Dir[File.join(ROOT, 'geometry_framing/core/*.rb')].sort.to_h { |path| [path, Digest::SHA256.file(path).hexdigest] }
detected = 0
MUTATIONS.each do |mutation|
  puts "\n突變 #{mutation[:id]}：拿掉「#{mutation[:rule]}」"
  Dir.mktmpdir('geometry-framing-mutation-') do |directory|
    # SU 轉接的純座標數學測試也會 require；複製來源不等於啟動 SketchUp。
    FileUtils.cp_r(File.join(ROOT, 'geometry_framing'), directory)
    isolated_tests = File.join(directory, 'test')
    FileUtils.mkdir_p(isolated_tests)
    (Dir[File.join(__dir__, 'test_*.rb')] + [File.join(__dir__, 'run.rb')]).each { |path| FileUtils.cp(path, isolated_tests) }
    FileUtils.cp_r(File.join(__dir__, 'fixtures'), isolated_tests)

    target = File.join(directory, 'geometry_framing/core', mutation[:file])
    source = File.read(target, encoding: 'UTF-8')
    unless source.scan(mutation[:before]).length == 1
      warn "突變 #{mutation[:id]} 的替換位置不是唯一；拒絕假裝成功。"
      exit 2
    end
    File.write(target, source.sub(mutation[:before], mutation[:after]), encoding: 'UTF-8')
    puts "實際替換：#{mutation[:before]} → #{mutation[:after]}"
    output, code = run([RbConfig.ruby, File.join(isolated_tests, 'run.rb'), '--seed', SEED, '--name', mutation[:test]])
    expected_failure = code == 1 && output.include?("規則：#{mutation[:rule]}") &&
                       output.match?(/1 runs, \d+ assertions, 1 failures, 0 errors, 0 skips/)
    if expected_failure
      detected += 1
      puts "已偵測：#{mutation[:id]}；對應測試變紅，失敗訊息指名規則。"
    else
      warn "未通過：#{mutation[:id]}；必須得到 exit_code=1、1 個具規則名稱的 assertion failure，不能是執行錯誤。"
    end
  end
end

unless originals.all? { |path, sha| Digest::SHA256.file(path).hexdigest == sha }
  warn '正式 core 檔案在突變執行期間改變，請重新執行。'
  exit 2
end
puts "\n突變結果：#{detected}/#{MUTATIONS.length} 個規則移除均被對應測試偵測；正式 core 未改動。"
exit(detected == MUTATIONS.length ? 0 : 1)
