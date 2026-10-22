# frozen_string_literal: true

require 'sketchup.rb'
require 'extensions.rb'

module GeometryFraming
  VERSION = '0.1.0' unless const_defined?(:VERSION)

  unless file_loaded?(__FILE__)
    extension = SketchupExtension.new('下角材', File.join(__dir__, 'geometry_framing', 'su', 'main'))
    extension.description = '平釘天花下角材與斷面設計；依已確認 demo 檢查後產生元件。'
    extension.version = VERSION
    extension.creator = 'ZhiQiYang'
    extension.copyright = '2026 ZhiQiYang'
    Sketchup.register_extension(extension, true)
    file_loaded(__FILE__)
  end
end
