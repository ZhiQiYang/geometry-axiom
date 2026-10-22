# frozen_string_literal: true

# ruby sketchup-plugin/test/record_evidence.rb [原始 demo HTML 路徑]
# 固定 seed，將每次真正執行的 stdout/stderr 與 exit code 保存；失敗仍完整保存。
require_relative 'run_mutations'

directory = File.join(__dir__, 'evidence')
FileUtils.mkdir_p(directory)
commands = {
  'minitest.txt' => [RbConfig.ruby, File.join(__dir__, 'run.rb'), '--seed', '20261013'],
  'mutation-runner-selftest.txt' => [RbConfig.ruby, File.join(__dir__, 'run_mutations.rb'), '--selftest'],
  'mutations.txt' => [RbConfig.ruby, File.join(__dir__, 'run_mutations.rb')]
}
commands = { 'demo_oracle.txt' => ['node', File.join(__dir__, 'demo_oracle.js'), ARGV.first] }.merge(commands) if ARGV.first
originals = FramingMutationRunner.source_hashes
source_digest = FramingMutationRunner.source_digest(originals)
failed = false
commands.each do |name, command|
  if name == 'mutations.txt'
    # runner 自己對每次基準／突變設定 timeout；不要外層提早殺 runner 遺留其子程序。
    output, status = Open3.capture2e(*command)
    result = { output: output.force_encoding(Encoding::UTF_8), exit_code: status.exitstatus, timed_out: false, launch_error: nil }
  else
    result = FramingMutationRunner.execute(command)
  end
  report = "Ruby：#{RUBY_DESCRIPTION}\n正式 core+su+test_su 來源 SHA-256：#{source_digest}\n命令：#{command.map(&:inspect).join(' ')}\n\n#{result[:output]}\nexit_code=#{result[:exit_code].inspect}\ntimeout=#{result[:timed_out]}\n"
  report += "啟動失敗：#{result[:launch_error]}\n" if result[:launch_error]
  File.write(File.join(directory, name), report, encoding: 'UTF-8')
  print report
  failed ||= !FramingMutationRunner.clean_success?(result)
end
unless originals == FramingMutationRunner.source_hashes
  warn '證據記錄期間 core+su+test_su 來源有變動；以上不能當成同一版的完成證據，請重跑。'
  exit 2
end
# 只更新本次命令的固定檔名，刻意保留 p076-*.txt 修前紅／修後綠的歷史證據。
exit(failed ? 1 : 0)
