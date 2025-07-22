from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from camera import Camera
    from ui import UI
    from procgen import ProcGen
    from sprite_manager import SpriteManager
    from chunk_manager import ChunkManager
    from input_manager import InputManager
    
import pygame as pg
from os import walk
from os.path import join
from math import ceil, floor, sin
from random import randint

from settings import *
from weather import Weather

class GraphicsEngine:
    def __init__(
        self, 
        screen: pg.Surface,
        cam: Camera,
        graphics: dict[str, list[pg.Surface]],
        ui: UI,
        sprite_manager: SpriteManager,
        chunk_manager: ChunkManager,
        input_manager: InputManager,
        player: Player,
        tile_map: np.ndarray, 
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str],
        current_biome: str,
        biome_order: dict[str, int],
    ):
        self.screen = screen
        self.cam = cam
        self.graphics = graphics
        self.ui = ui
        self.sprite_manager = sprite_manager
        self.chunk_manager = chunk_manager
        self.input_manager = input_manager
        self.player = player
        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.current_biome = current_biome
        self.biome_order = biome_order
        
        self.terrain = Terrain(
            self.screen, 
            self.graphics, 
            self.cam.offset, 
            self.chunk_manager,
            self.tile_map,
            self.tile_IDs,
            self.tile_IDs_to_names,
            self.sprite_manager.mining.mining_map,
            self.current_biome,
            self.biome_order,
            self.player
        )

        self.tool_animation = ToolAnimation(self.screen, self.render_item_held)
        self.weather = Weather(self.screen)

        # only render an equipped item while the sprite is in a given state
        self.item_render_states = {
            'pickaxe': {'mining', 'fighting'},
            'axe': {'chopping', 'fighting'}
        }

        # self.sprite_manager.<sprite group> -> self.<sprite_group>
        for name, group in self.sprite_manager.all_groups.items():
            setattr(self, name, group)

        self.tool_animation = ToolAnimation(self.screen, self.render_item_held)
        self.weather = Weather(screen)

        # only render an equipped item while the sprite is in a given state
        self.item_render_states = {
            'pickaxe': {'mining', 'fighting'},
            'axe': {'chopping', 'fighting'}
        }

        # self.sprite_manager.<sprite group> -> self.<sprite_group>
        for name, group in self.sprite_manager.all_groups.items():
            setattr(self, name, group)

    def animate_sprite(self, sprite: pg.sprite.Sprite, dt: float) -> None:
        if sprite.state not in {'idle', 'mining', 'chopping'}:
            sprite.frame_index += sprite.animation_speed[sprite.state] * dt
            if self.flip_sprite_x(sprite):
                sprite.facing_left = not sprite.facing_left

            sprite.image = pg.transform.flip(
                sprite.frames[sprite.state][int(sprite.frame_index % len(sprite.frames[sprite.state]))],
                not sprite.facing_left,
                False
            )
        else:
            image = sprite.frames['idle'][0]
            # added 'and sprite.facing_left' to prevent flipping left after lifting the right key
            sprite.image = image if not self.flip_sprite_x(sprite) and sprite.facing_left else pg.transform.flip(image, True, False)
        
    @staticmethod
    def flip_sprite_x(sprite: pg.sprite.Sprite) -> bool:
        '''signals when the sprite's facing & movement directions misalign'''
        return sprite.facing_left and sprite.direction.x > 0 or not sprite.facing_left and sprite.direction.x < 0
        
    def render_sprites(self, dt: float) -> None:
        all_sprites = self.sprite_manager.all_sprites
        for sprite in sorted(self.sprite_manager.get_sprites_in_radius(self.player.rect, all_sprites), key = lambda sprite: sprite.z):
            self.screen.blit(sprite.image, sprite.rect.topleft - self.cam.offset)
            groups = self.get_sprite_groups(sprite) 
            if groups: # the sprite isn't just a member of all_sprites
                self.render_group_action(groups, sprite, dt)

    def visible_check(self, sprite) -> bool:
        '''returns whether the sprite is within/outside the screen boundary'''
        return abs(sprite.rect.centerx - self.player.rect.centerx) < (RES[0] // 2) + 100

    def get_sprite_groups(self, sprite: pg.sprite.Sprite) -> set[str]:
        '''
        return every sprite group a given sprite is a member of
        in order to determine which rendering methods to pass the sprite into
        '''
        return set(group for group in self.sprite_manager.all_groups.values() if sprite in group)

    def render_group_action(self, groups: set[pg.sprite.Group], sprite: pg.sprite.Sprite, dt: float) -> None:
        '''
        call the rendering methods associated with specific sprite groups
        e.g only sprites in the animated_sprite group are passed to self.animated_sprite()
        '''
        if self.animated_sprites in groups:
            self.animate_sprite(sprite, dt)
                
        # TODO: this may need to be updated if more sprites can also hold objects
        if self.human_sprites in groups:
            self.render_item_held(dt)

    def render_item_held(self, dt: float) -> None:
        # TODO: this is unfinished
        for sprite in self.sprite_manager.human_sprites:
            self.update_active_item(sprite)

            if sprite.item_holding:
                item_category = self.get_item_category(sprite)
                if item_category:
                    if item_category in self.item_render_states.keys() and sprite.state in self.item_render_states[item_category]:
                        image = pg.transform.flip(self.graphics[item_category][sprite.item_holding], sprite.facing_left, False)
                        image_frame = self.get_item_animation(sprite, item_category, image, dt) # get the item's animation when in use
                        coords = sprite.rect.center - self.cam.offset + self.get_item_offset(item_category, sprite.facing_left)
                        rect = image_frame.get_rect(center = coords) if image_frame else image.get_rect(center = coords)
                        self.screen.blit(image_frame if image_frame else image, rect)

    def update_active_item(self, sprite: pg.sprite.Sprite) -> str:
        if sprite.item_holding != self.sprite_manager.active_items[sprite]:
            self.sprite_manager.active_items[sprite] = sprite.item_holding
    
    @staticmethod
    def get_item_category(sprite: pg.sprite.Sprite) -> str:
        '''removes the material name from the item_holding variable if applicable'''
        return sprite.item_holding.split()[-1] if ' ' in sprite.item_holding else None

    def get_item_animation(self, sprite: pg.sprite.Sprite, category: str, image: pg.Surface, dt: float) -> pg.Surface:
        match category:
            case 'pickaxe' | 'axe':
                if sprite.state in {'mining', 'chopping'}:
                    image = self.tool_animation.get_rotation(sprite, image, dt)
                    return image
        return image
    
    @staticmethod
    def get_item_offset(category, facing_left: bool) -> pg.Vector2:
        '''align the item with the sprite's arm'''
        match category:
            case 'pickaxe':
                return pg.Vector2(3 if facing_left else -3, 6) 
            case 'axe':
                return pg.Vector2(2 if facing_left else -2, -4)

    def update(
        self, 
        mouse_coords: tuple[int, int], 
        mouse_moving: bool, 
        click_states: dict[str, bool],
        current_biome: str,
        dt: float
    ) -> None:
        self.sprite_manager.update(dt)
        
        self.weather.update()
        # update the weather first to keep the sky behind the rest of the world
        self.terrain.update(current_biome)
        self.render_sprites(dt)
        
        self.ui.update(mouse_coords, mouse_moving, click_states)
        self.cam.update(target_coords = pg.Vector2(self.player.rect.center))


class Terrain:
    def __init__(
        self, 
        screen: pg.Surface, 
        graphics: dict[str, list[pg.Surface]], 
        cam_offset: pg.Vector2, 
        chunk_manager: ChunkManager,
        tile_map: np.ndarray,
        tile_IDs: dict[str, int],
        tile_IDs_to_names: dict[int, str],
        mining_map: dict[tuple[int, int], dict[str, int]],
        current_biome: str,
        biome_order: dict[str, int],
        player: Player
    ):
        self.screen = screen
        self.graphics = graphics
        self.cam_offset = cam_offset
        self.chunk_manager = chunk_manager

        self.tile_map = tile_map
        self.tile_IDs = tile_IDs
        self.tile_IDs_to_names = tile_IDs_to_names
        self.mining_map = mining_map

        self.current_biome = current_biome
        self.biome_order = biome_order

        self.player = player

        self.biome_x_offsets = {biome: self.biome_order[biome] * BIOME_WIDTH * TILE_SIZE for biome in self.biome_order.keys()}
        self.elev_data = self.get_elevation_data()
        self.biome_transition = BiomeTransition(self.graphics, self.render_bg_imgs)

    def get_tile_type(self, x: int, y: int) -> str:
        return self.tile_IDs_to_names.get(self.tile_map[x, y], 'obj extended')

    def get_terrain_type(self) -> str:
        '''just for getting a specific wall variant but could become more modular'''
        match self.current_biome:
            case 'highlands':
                return 'stone'

            case 'defiled':
                return 'defiled stone'

            case 'taiga':
                return 'dirt' if randint(0, 10) < 6 else 'stone'

            case 'desert':
                return 'sandstone'
                
            case 'underworld':
                return 'magma'

    def get_elevation_data(self) -> dict[str, int]:
        elev_params = BIOMES[self.current_biome]['elevation']
        top, bottom = elev_params['top'], elev_params['bottom']
        elev_data = {
            'range': (bottom - top) * TILE_SIZE,
            'underground span': (MAP_SIZE[1] * TILE_SIZE) - (bottom * TILE_SIZE), # minimum number of tiles from the bottom of the map to the surface
        }
        elev_data['landscape base'] = (bottom * TILE_SIZE) - (elev_data['range'] // 2.5)
        return elev_data

    def render_bg_imgs(self, bg_type: str, imgs_folder: dict[int, pg.Surface] = None) -> None:
        base_y = self.elev_data['landscape base']
        if not imgs_folder: # only provided for biome transitions
            imgs_folder = self.graphics[self.current_biome][bg_type]
        num_layers = len(imgs_folder)
        biome_x_offset = self.biome_x_offsets[self.current_biome]

        for i in range(num_layers):
            img = imgs_folder[i]
            img_width, img_height = img.get_width(), img.get_height()
            num_imgs_x = ceil(RES[0] / img_width) + 2

            if bg_type == 'landscape':
                layer_idx = num_layers - i - 1
                layer_offset_y = ((img_height // 4) * layer_idx) + img_height
                parallax_factor = 1.0 if num_layers < 2 else (i + 1) / num_layers
                scroll_x = self.cam_offset.x * parallax_factor
                start_x = floor((scroll_x - biome_x_offset) / img_width)
                for x in range(start_x, start_x + num_imgs_x):
                    self.screen.blit(img, ((biome_x_offset + x * img_width) - scroll_x, base_y - layer_offset_y - self.cam_offset.y))  
            else: # underground
                start_x = floor((self.cam_offset.x - biome_x_offset) / img_width)
                dist_y = self.elev_data['underground span']
                layer_dist_y = ceil(dist_y / num_layers)
                num_imgs_y = ceil(layer_dist_y / img_height)
                for x in range(start_x, start_x + num_imgs_x):
                    for y in range(num_imgs_y):
                        self.screen.blit(img, (biome_x_offset + (img_width * x), base_y + (img_height * y)) - self.cam_offset)

    def render_tiles(self) -> None:
        visible_chunks = self.chunk_manager.update()
        air_ID = self.tile_IDs['air']
        mining_map_keys = self.mining_map.keys()
        for coords in visible_chunks: # all visible tile coordinates
            for (x, y) in coords: # individual tile coordinates
                # ensure that the tile is within the map borders & is a solid tile
                if 0 <= x < MAP_SIZE[0] and 0 <= y < MAP_SIZE[1] and self.tile_map[x, y] != air_ID:
                    tile = self.get_tile_type(x, y)
                    if tile == 'obj extended': # to be ignored as far as rendering is concerned
                        continue 

                    elif tile == 'tree base':
                        tile = 'dirt' # otherwise the tile at the base of the tree won't be rendered

                    if (x, y) in mining_map_keys:
                        image = self.get_mined_tile_image(x, y)
                    else:
                        image = self.graphics[tile] if 'ramp' not in tile else self.graphics['ramps'][tile]
                    self.screen.blit(image, self.tile_pixel_convert(image.get_size(), x, y) - self.cam_offset)

    @staticmethod
    def tile_pixel_convert(image_size: tuple[int, int], x: int, y: int) -> pg.Vector2:
        if image_size == (TILE_SIZE, TILE_SIZE):
            return pg.Vector2(x * TILE_SIZE, y * TILE_SIZE)
        
        tile_size_offset = pg.Vector2(image_size[0] % TILE_SIZE, image_size[1] % TILE_SIZE) // 2
        return (pg.Vector2(x, y) * TILE_SIZE) + tile_size_offset

    def get_mined_tile_image(self, x: int, y: int) -> None:
        '''reduce the opacity of a given tile as it's mined away'''
        tile_image = self.graphics[self.get_tile_type(x, y)].copy()
        tile_image.set_alpha(170) 
        return tile_image

    def get_biome_status(self, current_biome: str) -> None:
        if current_biome != self.current_biome:
            self.biome_transition.previous_biome = self.current_biome
            self.current_biome = current_biome
            self.biome_transition.active = True

    def update(self, current_biome: str) -> None:
        self.get_biome_status(current_biome)
        if self.biome_transition.active:
            self.biome_transition.run(current_biome)
        else:
            self.render_bg_imgs('landscape')
            self.render_bg_imgs('underground')
        self.render_tiles()


class BiomeTransition:
    '''fade the new/old graphics in/out when crossing the border between biomes'''
    def __init__(self, graphics: dict[str, list[pg.Surface]], render_bg_imgs: callable):
        self.graphics = graphics
        self.render_bg_imgs = render_bg_imgs

        self.active = False
        self.previous_biome = None
        self.bg_types = ('landscape', 'underground')
        self.alphas_init = False
        self.alpha_factor = 3
        self.current_biome_min_alpha = 50
        
    def init_alphas(self, current_biome: str) -> None:
        for bg_type in self.bg_types:
            for img in self.graphics[self.previous_biome][bg_type].values():
                img.set_alpha(255) 

            for img in self.graphics[current_biome][bg_type].values():
                img.set_alpha(self.current_biome_min_alpha) 
            
            self.alphas_init = True

    def run(self, current_biome: str) -> None:
        if not self.alphas_init:
            self.init_alphas(current_biome)
            return
        
        for bg_type in self.bg_types:
            previous_biome_imgs = list(self.graphics[self.previous_biome][bg_type].values())
            current_biome_imgs = list(self.graphics[current_biome][bg_type].values())

            for img in previous_biome_imgs:
                new_alpha = max(0, img.get_alpha() - self.alpha_factor)
                img.set_alpha(new_alpha)
                self.active = new_alpha > 0 

            for img in current_biome_imgs:
                new_alpha = min(255, img.get_alpha() + self.alpha_factor)
                img.set_alpha(new_alpha)
                self.active = new_alpha < 255
            
            self.render_bg_imgs(bg_type, previous_biome_imgs)
            self.render_bg_imgs(bg_type, current_biome_imgs)

        if not self.active:
            self.alphas_init = False


class ToolAnimation:
    def __init__(self, screen: pg.Surface, render_item_held: callable):
        self.screen = screen
        self.render_item_held = render_item_held

    @staticmethod
    def get_rotation(sprite: pg.sprite.Sprite, image: pg.Surface, dt: float) -> pg.Surface:
        sprite.rotate_timer = getattr(sprite, "rotate_timer", 0.0) + dt
        angle = 45 * sin(sprite.rotate_timer * 10)
        return pg.transform.rotate(image, -angle if not sprite.facing_left else angle) # negative angles rotate clockwise