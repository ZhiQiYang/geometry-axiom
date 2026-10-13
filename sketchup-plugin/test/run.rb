# frozen_string_literal: true

# ruby sketchup-plugin/test/run.rb --seed 20261013
Dir[File.join(__dir__, 'test_*.rb')].sort.each { |path| require path }
