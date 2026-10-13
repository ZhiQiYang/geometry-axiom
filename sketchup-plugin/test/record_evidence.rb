# frozen_string_literal: true

# ruby sketchup-plugin/test/record_evidence.rb [原始 demo HTML 路徑]
# 固定 seed，將每次真正執行的 stdout/stderr 與 exit code 保存；失敗仍完整保存。
require 'fileutils'
require 'open3'
require 'rbconfig'

directory = File.join(__dir__, 'evidence')
FileUtils.mkdir_p(directory)
commands = {
  'minitest.txt' => [RbConfig.ruby, File.join(__dir__, 'run.rb'), '--seed', '20261013'],
  'mutations.txt' => [RbConfig.ruby, File.join(__dir__, 'run_mutations.rb')]
}
commands = { 'demo_oracle.txt' => ['node', File.join(__dir__, 'demo_oracle.js'), ARGV.first] }.merge(commands) if ARGV.first
failed = false
commands.each do |name, command|
  output, status = Open3.capture2e(*command)
  output = output.force_encoding(Encoding::UTF_8)
  report = "Ruby：#{RUBY_DESCRIPTION}\n命令：#{command.map(&:inspect).join(' ')}\n\n#{output}\nexit_code=#{status.exitstatus.inspect}\n"
  File.write(File.join(directory, name), report, encoding: 'UTF-8')
  print report
  failed ||= !status.success?
end
exit(failed ? 1 : 0)
