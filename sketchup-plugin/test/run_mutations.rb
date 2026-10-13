# frozen_string_literal: true

# ruby sketchup-plugin/test/run_mutations.rb [--selftest]
# 隔離複本實際移除規則；正式程式沒有突變開關。
require 'digest'
require 'fileutils'
require 'json'
require 'open3'
require 'rbconfig'
require 'tmpdir'

module FramingMutationRunner
  ROOT = File.expand_path('..', __dir__)
  SEED = '20261013'
  COMMAND_TIMEOUT = 60
  MUTATIONS = [
    { id: 'edge_shift', rule: '收邊挪縫', file: 'core/panel_axis.rb',
      before: 'if !seams.empty? && seams.last > limit + 1e-9', after: 'if false',
      tests: { 'test_edge_shift_rule' => '規則：收邊挪縫' } },
    { id: 'column_edge', rule: '柱邊料', file: 'core/flat_ceiling.rb',
      before: 'next if ri.positive? && !p[:colEdge]', after: 'next if ri.positive?',
      tests: { 'test_column_edge_rule' => '規則：柱邊料' } },
    { id: 'primary_continuity', rule: '主支不可斷開', file: 'core/checks.rb',
      before: 'continuity_ok = g[:clashes].empty?', after: 'continuity_ok = true',
      tests: { 'test_primary_continuity_rule' => '規則：主支不可斷開' } },
    { id: 'd1_integer_mm', rule: 'D1 整數 mm', file: 'su/selection.rb',
      before: 'rounded = points.map { |point| point.map { |value| value.round } } # D1_INTEGER_MM_PROJECTION',
      after: 'rounded = points.map(&:dup) # D1_INTEGER_MM_PROJECTION',
      tests: {
        'test_d1_integer_mm_longest_edge_projection_notch_3000_angles' => 'D1 整數 mm',
        'test_d1_integer_mm_projection_3664_by_3668_400_angles_keeps_inventory' => 'D1 整數 mm'
      } },
    { id: 'obstacle_generated_filter', rule: '自產物排除', file: 'su/obstacles.rb',
      before: 'return false if path.any? { |entity| generated?(entity) }', after: 'return false if false',
      tests: { 'test_previous_plugin_result_is_not_a_beam_on_rerun' => 'P076 M2 自產物排除' } },
    { id: 'obstacle_visibility_filter', rule: '障礙可見性', file: 'su/obstacles.rb',
      before: 'return false unless path.all? { |entity| visible?(entity) }', after: 'return false unless true',
      tests: {
        'test_hidden_or_tag_disabled_entities_are_excluded' => 'P076 M2 可見性',
        'test_hierarchy_visibility_and_tag_folder_visibility_are_respected' => 'P076 M2 可見性'
      } },
    { id: 'dialog_lifecycle', rule: '對話框生命週期', file: 'su/dialog.rb',
      before: 'dialog.set_on_closed { @dialog = nil if @dialog.equal?(dialog) }',
      after: 'dialog.set_on_closed { @dialog = nil }',
      tests: { 'test_delayed_close_preserves_the_current_dialog' => '規則：對話框生命週期' } },
    { id: 'material_preservation', rule: '既有材質保留', file: 'su/builder.rb',
      before: 'return value if value',
      after: "value.color = COLORS.fetch(role) if value\n        return value if value",
      tests: {
        'test_second_ceiling_keeps_the_first_ceiling_user_material_color' => 'P076 材質保留',
        'test_existing_named_material_is_reused_without_any_color_write' => 'P076 材質保留'
      } },
    { id: 'acceptance_entities_api', rule: 'B1 Entities API', file: 'test_su/run_all.rb',
      before: '@model.entities.length.zero?', after: '@model.entities.empty?',
      tests: { 'test_b1_empty_model_reaches_first_fixture_transaction_without_entities_empty' => 'B1 Entities API' } }
  ].freeze

  module_function

  # 到期只終止本次建立的程序樹；B1 的隔離 Ruby 子程序也不會遺留。
  # timeout 與啟動失敗都不能算偵測成功。
  def execute(command, timeout: COMMAND_TIMEOUT)
    result = { output: '', exit_code: nil, timed_out: false, launch_error: nil }
    group_options = windows? ? { new_pgroup: true } : { pgroup: true }
    Open3.popen2e(*command, **group_options) do |input, output, process|
      input.close
      reader = Thread.new do
        output.read.force_encoding(Encoding::UTF_8)
      rescue IOError
        ''
      end
      unless process.join(timeout)
        result[:timed_out] = true
        begin
          if windows?
            killer = Process.spawn('taskkill', '/PID', process.pid.to_s, '/T', '/F', out: File::NULL, err: File::NULL)
            Process.wait(killer)
          else
            Process.kill('KILL', -process.pid)
          end
        rescue Errno::ESRCH
          # 到期與程序自行結束可能同時發生；仍以 timeout 記錄。
        end
        process.join(5)
      end
      result[:exit_code] = process.value.exitstatus unless process.alive?
      unless reader.join(5)
        result[:timed_out] = true
        output.close unless output.closed?
        reader.join(1)
      end
      result[:output] = reader.value unless reader.alive?
    end
    result
  rescue SystemCallError, IOError => error
    result.merge(launch_error: "#{error.class}: #{error.message}")
  end

  def windows?
    /mswin|mingw|cygwin/.match?(RbConfig::CONFIG.fetch('host_os'))
  end

  def display_run(command, timeout: COMMAND_TIMEOUT)
    puts "命令：#{command.map(&:inspect).join(' ')}"
    result = execute(command, timeout: timeout)
    print result[:output]
    puts "exit_code=#{result[:exit_code].inspect}"
    puts "timeout=#{result[:timed_out]}"
    puts "啟動失敗：#{result[:launch_error]}" if result[:launch_error]
    result
  end

  def clean_success?(result)
    result[:exit_code] == 0 && !result[:timed_out] && result[:launch_error].nil?
  end

  def expected_failures?(result, tests)
    return false unless result[:exit_code] == 1 && !result[:timed_out] && result[:launch_error].nil?

    output = result[:output]
    summary = output.scan(/^(\d+) runs, (\d+) assertions, (\d+) failures, (\d+) errors, (\d+) skips\s*$/).last
    return false unless summary && summary.values_at(0, 2, 3, 4).map(&:to_i) == [tests.length, tests.length, 0, 0]

    # 每個指定測試都要各自變紅，且該 failure 區塊本身要含規則訊息。
    failures = output.scan(/^\s*\d+\) Failure:\r?\n(.*?)(?=^\s*\d+\) (?:Failure|Error):|^\d+ runs,|\z)/m).flatten
    return false unless failures.length == tests.length

    tests.all? do |test, marker|
      matching = failures.select { |failure| failure.lines.first.to_s.match?(/##{Regexp.escape(test)}(?:\s|\[|:|$)/) }
      matching.length == 1 && matching.first.include?(marker)
    end
  end

  def source_hashes
    files = Dir[File.join(ROOT, 'geometry_framing/{core,su}/**/*.rb')] + Dir[File.join(ROOT, 'test_su/**/*.rb')]
    files.sort.to_h do |path|
      [path.delete_prefix(ROOT + '/'), Digest::SHA256.file(path).hexdigest]
    end
  end

  def source_digest(hashes = source_hashes)
    Digest::SHA256.hexdigest(JSON.generate(hashes))
  end

  def copy_tests(directory)
    FileUtils.cp_r(File.join(ROOT, 'geometry_framing'), directory)
    FileUtils.cp_r(File.join(ROOT, 'test_su'), directory)
    isolated_tests = File.join(directory, 'test')
    FileUtils.mkdir_p(isolated_tests)
    (Dir[File.join(__dir__, 'test_*.rb')] + [File.join(__dir__, 'run.rb')]).each { |path| FileUtils.cp(path, isolated_tests) }
    FileUtils.cp_r(File.join(__dir__, 'fixtures'), isolated_tests)
    isolated_tests
  end

  def run_mutations
    puts "Ruby：#{RUBY_DESCRIPTION}"
    puts '基準線：先確認未改規則的完整 minitest 全過'
    baseline = display_run([RbConfig.ruby, File.join(__dir__, 'run.rb'), '--seed', SEED])
    unless clean_success?(baseline)
      warn '基準線失敗／受阻；不把既有失敗、環境或 timeout 算成突變被偵測。'
      return 2
    end

    detected = 0
    MUTATIONS.each do |mutation|
      puts "\n突變 #{mutation[:id]}：拿掉「#{mutation[:rule]}」"
      Dir.mktmpdir('geometry-framing-mutation-') do |directory|
        isolated_tests = copy_tests(directory)
        relative = mutation[:file].start_with?('test_su/') ? mutation[:file] : File.join('geometry_framing', mutation[:file])
        target = File.expand_path(relative, directory)
        allowed = ['geometry_framing/core', 'geometry_framing/su', 'test_su'].map { |path| File.expand_path(path, directory) + '/' }
        unless allowed.any? { |path| target.start_with?(path) } && File.file?(target)
          warn "突變 #{mutation[:id]} 路徑不在隔離來源內或不存在。"
          return 2
        end
        source = File.read(target, encoding: 'UTF-8')
        unless source.scan(mutation[:before]).length == 1
          warn "突變 #{mutation[:id]} 的替換位置不是唯一；拒絕假裝成功。"
          return 2
        end
        File.write(target, source.sub(mutation[:before], mutation[:after]), encoding: 'UTF-8')
        puts "來源：#{mutation[:file]}"
        puts "實際替換：#{mutation[:before]} → #{mutation[:after]}"
        names = mutation[:tests].keys.map { |name| Regexp.escape(name) }.join('|')
        filter = "/\\A(?:#{names})\\z/"
        result = display_run([RbConfig.ruby, File.join(isolated_tests, 'run.rb'), '--seed', SEED, '--name', filter])
        if expected_failures?(result, mutation[:tests])
          detected += 1
          puts "已偵測：#{mutation[:id]}；#{mutation[:tests].length} 個指定測試各自變紅，失敗訊息指名規則。"
        else
          warn "未通過：#{mutation[:id]}；必須 exit_code=1、#{mutation[:tests].length} 個具名規則 assertion failures、零 errors/skips、無 timeout。"
        end
      end
    end
    puts "\n突變結果：#{detected}/#{MUTATIONS.length} 個規則移除均被對應測試偵測。"
    detected == MUTATIONS.length ? 0 : 1
  end

  def selftest
    tests = { 'test_first' => '規則：D1 整數mm', 'test_second' => '規則：D1 整數mm' }
    output = "  1) Failure:\nExample#test_first [a.rb:1]:\n規則：D1 整數mm\n\n  2) Failure:\nExample#test_second [a.rb:2]:\n規則：D1 整數mm\n\n2 runs, 2 assertions, 2 failures, 0 errors, 0 skips\n"
    good = { output: output, exit_code: 1, timed_out: false, launch_error: nil }
    checks = {
      '兩個具名 assertion failure' => expected_failures?(good, tests),
      '其中一個測試沒有規則訊息必須拒絕' => !expected_failures?(good.merge(output: output.sub('規則：D1 整數mm', '沒有規則名稱')), tests),
      '少跑一個測試必須拒絕' => !expected_failures?(good.merge(output: output.sub('2 runs', '1 runs')), tests),
      '測試名稱不符必須拒絕' => !expected_failures?(good.merge(output: output.sub('#test_first', '#test_wrong')), tests),
      'error 不得當成 assertion failure' => !expected_failures?(good.merge(output: output.sub('0 errors', '1 errors')), tests),
      'skip 不得算成功' => !expected_failures?(good.merge(output: output.sub('0 skips', '1 skips')), tests),
      'exit 0 不是突變失敗' => !expected_failures?(good.merge(exit_code: 0), tests),
      'timeout 不能冒充成功' => !expected_failures?(good.merge(timed_out: true), tests)
    }
    load_error = execute([RbConfig.ruby, '-e', "raise LoadError, '故意驗證 runner'"], timeout: 10)
    checks['真實 LoadError exit 1 必須拒絕'] = load_error[:exit_code] == 1 && !expected_failures?(load_error, tests)
    timed = execute([RbConfig.ruby, '-e', 'sleep 5'], timeout: 0.2)
    checks['真實超時必須終止且拒絕'] = timed[:timed_out] && !expected_failures?(timed, tests)
    checks.each { |name, ok| puts "#{ok ? '通過' : '失敗'}：#{name}" }
    puts "runner 誠實性自測：#{checks.count { |_name, ok| ok }}/#{checks.length}"
    checks.values.all? ? 0 : 1
  end

  def main
    return selftest if ARGV == ['--selftest']
    unless ARGV.empty?
      warn '用法：ruby sketchup-plugin/test/run_mutations.rb [--selftest]'
      return 2
    end

    originals = source_hashes
    puts "正式 core+su+test_su 來源 SHA-256：#{source_digest(originals)}"
    status = begin
      run_mutations
    rescue StandardError => error
      warn "突變執行受阻：#{error.class}: #{error.message}"
      2
    end
    unless originals == source_hashes
      warn '正式 core+su+test_su 檔案在執行期間新增、刪除或改變，請重新執行。'
      return 2
    end
    puts '正式 core+su+test_su 來源集合與每檔 SHA-256 均未改動。'
    status
  end
end

exit FramingMutationRunner.main if $PROGRAM_NAME == __FILE__
