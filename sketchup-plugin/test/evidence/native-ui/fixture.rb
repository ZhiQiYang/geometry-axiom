# frozen_string_literal: true
require 'json'
require 'time'

# Only creates named fixtures in an empty model. Does not preview or generate.
module GeometryFramingUXFixed
  extend self
  OUTPUT = __dir__

  def setup
    @model = Sketchup.active_model
    raise 'Open an empty SketchUp 2026 model first.' unless Sketchup.version.to_i == 26 && @model.entities.length.zero? && @model.active_path.nil?
    @faces = {}
    @model.start_operation('下角材 UX 修正驗收夾具', true)
    make_face('A', 5000, 4800, 2500, 0)
    make_face('B', 3200, 2080, 2800, 12000)
    make_face('K', 3200, 2080, 2500, 22000, [[1400, 880], [1700, 880], [1700, 1180], [1400, 1180]])
    base, z0 = 30000, 2800
    @profile = @model.entities.add_group
    @profile.name = 'UX-P 斷面折線'
    points = [[467, 0], [467, 148], [743, 148], [743, 351], [0, 351]]
    @profile_edges = @profile.entities.add_edges(points.map { |u, v| [(base + u).mm, 0, (z0 - v).mm] })
    slab = @model.entities.add_group
    slab.name = 'UX-P 樓板接面'
    slab.entities.add_face([[-100, -100], [1000, -100], [1000, 2600], [-100, 2600]].map { |x, y| [(base+x).mm, y.mm, z0.mm] })
    wall = @model.entities.add_group
    wall.name = 'UX-P 牆接面'
    wall.entities.add_face([[-100, 2300], [2600, 2300], [2600, 2850], [-100, 2850]].map { |y, z| [base.mm, y.mm, z.mm] })
    @model.commit_operation
    @model.active_view.camera = Sketchup::Camera.new([16000.mm, -22000.mm, 26000.mm], [15000.mm, 0, 2000.mm], Z_AXIS)
    select('A')
    GeometryFraming::SU::Dialog.show('flat')
    puts 'UX fixed fixtures ready. select A/B/K/P changes selection only; capture(label) is read-only.'
  end

  def make_face(label, w, h, z, offset, hole = nil)
    group = @model.entities.add_group
    group.name = "UX-#{label} #{w}×#{h}／Z#{z}"
    group.entities.add_face([[0,0,z],[w,0,z],[w,-h,z],[0,-h,z]].map { |point| point.map(&:mm) })
    if hole
      hole_face = group.entities.add_face(hole.map { |x,y| [x.mm, -y.mm, z.mm] })
      hole_face.erase!
    end
    face = group.entities.grep(Sketchup::Face).find { |f| f.loops.length == (hole ? 2 : 1) }
    raise "Could not create fixture #{label}" unless face
    group.transformation = Geom::Transformation.translation([offset.mm, 0, 0])
    @faces[label] = {group: group, face: face}
  end

  def select(label)
    raise 'Wrong model.' unless Sketchup.active_model == @model
    if label == 'P'
      @model.active_path = [@profile]
      @model.selection.clear
      @model.selection.add(@profile_edges)
    else
      fixture = @faces.fetch(label)
      @model.active_path = [fixture[:group]]
      @model.selection.clear
      @model.selection.add(fixture[:face])
    end
    @model.active_view.zoom(@model.selection)
    puts "Selected fixture #{label}; no plugin preview or generation was invoked."
  end

  def capture(label)
    raise 'Wrong model.' unless Sketchup.active_model == @model
    raise 'Invalid evidence label.' unless /\A[a-z0-9_-]+\z/.match?(label)
    path = File.join(OUTPUT, "#{label}.json")
    raise 'Evidence already exists.' if File.exist?(path)
    groups = @model.entities.grep(Sketchup::Group).filter_map do |group|
      mode = group.get_attribute('GeometryFraming', 'mode')
      next unless mode
      input = JSON.parse(group.get_attribute('GeometryFraming', 'input', '{}'))
      source = mode == 'profile' ? 'P' : @faces.find { |_, f| f[:face].persistent_id == input['source_id'] }&.first
      bounds = group.bounds
      { id: group.persistent_id, name: group.name, mode: mode, source: source,
        params: JSON.parse(group.get_attribute('GeometryFraming', 'params', '{}')),
        input: input, min: bounds.min.to_a.map(&:to_mm), max: bounds.max.to_a.map(&:to_mm),
        counts: group.entities.grep(Sketchup::Group).to_h { |r| [r.get_attribute('GeometryFraming','role'), r.entities.grep(Sketchup::ComponentInstance).length] } }
    end
    data = {label: label, utc: Time.now.utc.iso8601(6), sketchup: Sketchup.version, ruby: RUBY_VERSION,
            path: (@model.active_path || []).map(&:persistent_id), selection: @model.selection.map(&:persistent_id), groups: groups}
    File.write(path, JSON.pretty_generate(data), encoding: 'UTF-8')
    puts "Saved read-only native evidence #{path}"
    data
  end
end

GeometryFramingUXFixed.setup
