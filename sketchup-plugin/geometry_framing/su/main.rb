# frozen_string_literal: true

require 'sketchup.rb'
require_relative '../core/flat_ceiling'
require_relative '../core/profile'
require_relative 'selection'
require_relative 'builder'
require_relative 'dialog'

module GeometryFraming
  module SU
    unless file_loaded?(__FILE__)
      menu = UI.menu('Extensions').add_submenu('下角材')
      menu.add_item('平釘天花下角材') { Dialog.show('flat') }
      menu.add_item('斷面設計') { Dialog.show('profile') }
      file_loaded(__FILE__)
    end
  end
end
