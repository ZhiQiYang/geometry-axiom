# frozen_string_literal: true

# Only Ruby / SketchUp API. Run in a separate, empty SketchUp 2026 model.
# ENV['GEOMETRY_FRAMING_NATIVE_SUITE'] = 'workflow' or 'full'
# ENV['GEOMETRY_FRAMING_RUNTIME_ROOT'] may point at an extracted RBZ directory.
# ENV['GEOMETRY_FRAMING_RBZ'] may point at the corresponding original RBZ.
require 'sketchup.rb'
require 'json'
require 'digest'
require 'fileutils'
require 'securerandom'

module GeometryFramingNativeAudit
  class Tee
    def initialize(original, stream)
      @original, @stream = original, stream
    end

    def write(value)
      text = value.to_s
      @stream.write(text)
      @stream.flush
      @original.write(text)
      text.bytesize
    end

    def puts(*values)
      values = [''] if values.empty?
      values.each { |value| write(value.to_s.end_with?("\n") ? value.to_s : "#{value}\n") }
      nil
    end

    def print(*values)
      values.each { |value| write(value) }
      nil
    end

    def flush
      @stream.flush
      @original.flush if @original.respond_to?(:flush)
      self
    end

    def method_missing(name, *args, &block) = @original.public_send(name, *args, &block)
    def respond_to_missing?(name, private = false) = @original.respond_to?(name, private)
  end

  class << self
    def hashes(directory)
      Dir[File.join(directory, '**', '*')].select { |path| File.file?(path) }.sort.to_h do |path|
        [path.delete_prefix(directory + '/'), Digest::SHA256.file(path).hexdigest]
      end
    end

    def save_json(name, value)
      File.write(File.join(@out, name), JSON.pretty_generate(value), encoding: 'UTF-8')
    end

    def completed(error = nil)
      return if @finished

      @finished = true
      result_path = File.join(@suite_out, 'result.json')
      result = File.file?(result_path) ? JSON.parse(File.read(result_path, encoding: 'UTF-8')) : {}
      after = hashes(File.join(@snapshot, 'geometry_framing'))
      source_same = after == @source_hashes && Digest::SHA256.file(@loader).hexdigest == @loader_hash
      exit_code = error || !source_same ? 1 : result.fetch('exit_code', 1)
      first_failure = error ? "#{error.class}: #{error.message}" : Array(result['log']).find { |line| line.start_with?('FAIL') }
      first_failure ||= 'runtime source changed during native execution' unless source_same
      first_failure ||= 'suite result.json was not written' if result.empty?
      report = @metadata.merge('semantic_exit_code' => exit_code, 'passed' => exit_code.zero?,
                               'source_unchanged' => source_same, 'first_failure' => first_failure,
                               'suite_result' => result, 'finished_at' => Time.now.iso8601)
      report['driver_error_backtrace'] = error.backtrace if error
      save_json('audit-result.json', report)
      puts("NATIVE AUDIT #{exit_code.zero? ? 'PASS' : 'FAIL'} semantic_exit_code=#{exit_code} first_failure=#{first_failure.inspect} evidence=#{@out}")
    ensure
      if @finished && @original_stdout
        $stdout, $stderr = @original_stdout, @original_stderr
        @stream.close unless @stream.closed?
        @original_stdout = nil
      end
      @running = false if @finished
    end

    def run
      # Keep this guard outside the current run's error-finalization handler.
      raise 'A previous native audit is still running.' if @running

      execute_audit
    end

    def execute_audit
      suite = ENV.fetch('GEOMETRY_FRAMING_NATIVE_SUITE', 'workflow')
      raise 'Suite must be workflow or full.' unless %w[workflow full].include?(suite)
      model = Sketchup.active_model
      raise 'Please open a separate empty model; this driver never clears a model.' unless model.entities.length.zero? && model.active_path.nil?
      raise 'SketchUp 2026 is required.' unless Sketchup.version.to_i == 26

      require 'time'
      runtime_root = File.expand_path(ENV.fetch('GEOMETRY_FRAMING_RUNTIME_ROOT', 'D:/geometry-axiom/sketchup-plugin'))
      test_root = 'D:/geometry-axiom/sketchup-plugin/test_su'
      rbz = ENV['GEOMETRY_FRAMING_RBZ']
      rbz = File.expand_path(rbz) if rbz && !rbz.empty?
      raise "RBZ does not exist: #{rbz}" if rbz && !File.file?(rbz)
      runtime = File.join(runtime_root, 'geometry_framing')
      raise "Runtime is missing: #{runtime}" unless File.file?(File.join(runtime, 'su/main.rb'))
      loader_source = File.join(runtime_root, 'geometry_framing.rb')
      raise "Extension loader is missing: #{loader_source}" unless File.file?(loader_source)

      token = "#{Time.now.strftime('%Y%m%d-%H%M%S')}-#{Process.pid}-#{SecureRandom.hex(3)}"
      @out = File.join(Sketchup.temp_dir, "geometry-framing-native-#{suite}-#{token}")
      @snapshot = File.join(@out, 'source')
      @suite_out = File.join(@out, 'suite')
      FileUtils.mkdir_p([@snapshot, @suite_out])
      FileUtils.cp_r(runtime, @snapshot)
      @loader = File.join(@snapshot, 'geometry_framing.rb')
      FileUtils.cp(loader_source, @loader)
      @loader_hash = Digest::SHA256.file(@loader).hexdigest
      FileUtils.cp_r(test_root, @snapshot)
      @source_hashes = hashes(File.join(@snapshot, 'geometry_framing'))
      suite_file = suite == 'full' ? 'run_all.rb' : 'run_workflow_regressions.rb'
      script = File.join(@snapshot, 'test_su', suite_file)
      @metadata = { 'suite' => suite, 'started_at' => Time.now.iso8601, 'sketchup' => Sketchup.version,
                    'ruby' => RUBY_DESCRIPTION, 'runtime_source' => runtime_root, 'snapshot' => @snapshot,
                    'source_sha256' => Digest::SHA256.hexdigest(JSON.generate(@source_hashes)),
                    'loader_sha256' => @loader_hash,
                    'source_files' => @source_hashes, 'suite_sha256' => Digest::SHA256.file(script).hexdigest,
                    'rbz_path' => rbz, 'rbz_sha256' => rbz && Digest::SHA256.file(rbz).hexdigest }
      save_json('audit-start.json', @metadata)
      @finished = false
      @running = true
      @original_stdout, @original_stderr = $stdout, $stderr
      @stream = File.open(File.join(@out, 'stdout-stderr.txt'), 'w:UTF-8')
      $stdout, $stderr = Tee.new(@original_stdout, @stream), Tee.new(@original_stderr, @stream)
      puts("NATIVE AUDIT START suite=#{suite} evidence=#{@out}")
      if defined?(GeometryFraming::SU::Dialog)
        dialog = GeometryFraming::SU::Dialog
        dialog.instance_variable_get(:@watch)&.stop
        dialog.instance_variable_get(:@dialog)&.close
        dialog.instance_variables.each { |name| dialog.remove_instance_variable(name) }
      end
      # Preserve the namespace objects used by existing menu closures, but remove
      # every prior runtime child so deleted methods/constants cannot survive reload.
      if defined?(GeometryFraming)
        %i[Core SU].each do |name|
          next unless GeometryFraming.const_defined?(name, false)

          namespace = GeometryFraming.const_get(name, false)
          namespace.constants(false).each { |child| namespace.send(:remove_const, child) }
          namespace.singleton_methods(false).each { |method| namespace.singleton_class.send(:remove_method, method) }
          (namespace.instance_methods(false) + namespace.private_instance_methods(false)).uniq.each do |method|
            namespace.send(:remove_method, method)
          end
        end
      end

      # The unique snapshot path ensures require cannot reuse an older loaded file.
      # Existing menu callbacks remain; this audit must not register another menu.
      main = File.join(@snapshot, 'geometry_framing/su/main.rb')
      file_loaded(@loader)
      GeometryFraming.send(:remove_const, :VERSION) if defined?(GeometryFraming) && GeometryFraming.const_defined?(:VERSION, false)
      require @loader
      file_loaded(main)
      require main
      unless GeometryFraming.const_defined?(:Acceptance, false)
        GeometryFraming.const_set(:Acceptance, Module.new)
      end
      name = suite == 'full' ? :Runner : :WorkflowRunner
      acceptance = GeometryFraming::Acceptance
      acceptance.send(:remove_const, name) if acceptance.const_defined?(name, false)
      runner_class = Class.new
      acceptance.const_set(name, runner_class)
      finish_hook = Module.new do
        define_method(:finish) do |*args|
          value = super(*args)
          GeometryFramingNativeAudit.completed
          value
        rescue Exception => error
          GeometryFramingNativeAudit.completed(error)
          raise
        end
      end
      runner_class.prepend(finish_hook)
      ENV[suite == 'full' ? 'GEOMETRY_FRAMING_SU_OUTPUT' : 'GEOMETRY_FRAMING_WORKFLOW_OUTPUT'] = @suite_out
      load script
      puts("NATIVE AUDIT LOAD RETURNED; full suite may still be waiting for native undo callbacks. evidence=#{@out}") unless @finished
      @out
    rescue Exception => error
      if @running && @stream && !@stream.closed?
        warn("NATIVE DRIVER ERROR #{error.class}: #{error.message}\n#{error.backtrace.join("\n")}")
        completed(error)
      else
        raise
      end
    end
  end
end

GeometryFramingNativeAudit.run
