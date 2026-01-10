from PySide6.QtWidgets import QStackedWidget, QWidget, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QPoint, QEasingCurve, QParallelAnimationGroup, QAbstractAnimation
from PySide6.QtGui import QPixmap, QPainter

class AnimatedStackedWidget(QStackedWidget):
    """
    A QStackedWidget that slides the new widget in and the old one out.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_direction = Qt.Horizontal
        self.m_speed = 300 # Duration in ms
        self.m_animation_type = QEasingCurve.OutCubic
        self.m_now_animated = False
        self.m_active = True

    def setSpeed(self, speed):
        self.m_speed = speed

    def setAnimation(self, animation_type):
        self.m_animation_type = animation_type

    def setCurrentIndex(self, index):
        if not self.m_active:
            super().setCurrentIndex(index)
            return

        if self.m_now_animated:
            # If already animating, just jump to end state or ignore.
            # For simplicity, we ignore or force finish.
            # But normally we just let it finish or queue. 
            # We'll just force call super which might snap.
            super().setCurrentIndex(index)
            return

        if self.currentIndex() == index:
            return

        # Indices
        current_idx = self.currentIndex()
        next_idx = index
        
        # Widgets
        current_widget = self.currentWidget()
        next_widget = self.widget(index)
        
        if not current_widget or not next_widget:
            super().setCurrentIndex(index)
            return

        # Calculate direction
        # If we assume tabs are ordered 0..N, then:
        # index > current -> Slide Left (Next comes from Right)
        # index < current -> Slide Right (Next comes from Left)
        offset_x = self.frameRect().width()
        offset_y = self.frameRect().height()
        
        if index > current_idx:
            # Slide Left: Next comes from Right (+width) to 0
            # Current goes from 0 to Left (-width)
            direction = 1
        else:
            # Slide Right: Next comes from Left (-width) to 0
            # Current goes from 0 to Right (+width)
            direction = -1

        p_current = QPoint(0, 0)
        p_next_start = QPoint(offset_x * direction, 0)
        p_current_end = QPoint(-offset_x * direction, 0)
        
        # Prepare Next Widget
        next_widget.setGeometry(0, 0, offset_x, offset_y)
        # We need to make next widget visible but not strictly "current" in stacked logic yet,
        # but QStackedWidget only shows one.
        # Trick: We capture pixmaps and animate labels.
        
        # 1. Render widgets to pixmaps
        pixmap_current = QPixmap(current_widget.size())
        current_widget.render(pixmap_current)
        
        pixmap_next = QPixmap(next_widget.size())
        # To render next widget correctly, it might need to be shown/resized. 
        # Usually stacked widget handles resize.
        # We temporarily set it to current to force layout/paint, capture, then switch back?
        # Or just trust it.
        # Better approach for QStackedWidget:
        # Just use the pixmaps.
        
        # However, next_widget isn't visible, so render might be empty if we don't handle it.
        # We can force resize.
        next_widget.resize(current_widget.size())
        # We might need to ensure it has polished.
        next_widget.render(pixmap_next)

        # 2. Create Overlay Widget for Animation
        self.anim_widget = QWidget(self)
        self.anim_widget.resize(self.size())
        # Raise it
        self.anim_widget.raise_()
        self.anim_widget.show()
        
        # Labels for pixmaps
        self.lbl_current = QLabel(self.anim_widget)
        self.lbl_current.setPixmap(pixmap_current)
        self.lbl_current.resize(self.size())
        self.lbl_current.show()
        self.lbl_current.move(p_current)
        
        self.lbl_next = QLabel(self.anim_widget)
        self.lbl_next.setPixmap(pixmap_next)
        self.lbl_next.resize(self.size())
        self.lbl_next.show()
        self.lbl_next.move(p_next_start)
        
        # 3. Create Animations
        self.anim_group = QParallelAnimationGroup()
        
        anim1 = QPropertyAnimation(self.lbl_current, b"pos")
        anim1.setDuration(self.m_speed)
        anim1.setEasingCurve(self.m_animation_type)
        anim1.setStartValue(p_current)
        anim1.setEndValue(p_current_end)
        
        anim2 = QPropertyAnimation(self.lbl_next, b"pos")
        anim2.setDuration(self.m_speed)
        anim2.setEasingCurve(self.m_animation_type)
        anim2.setStartValue(p_next_start)
        anim2.setEndValue(QPoint(0, 0))
        
        self.anim_group.addAnimation(anim1)
        self.anim_group.addAnimation(anim2)
        
        self.anim_group.finished.connect(self.on_animation_finished)
        
        self.m_now_animated = True
        self.m_next_idx = index
        
        # Start Animation
        self.anim_group.start(QAbstractAnimation.DeleteWhenStopped)

    def on_animation_finished(self):
        # Clean up
        super().setCurrentIndex(self.m_next_idx)
        self.lbl_current.hide()
        self.lbl_next.hide()
        self.anim_widget.hide()
        self.anim_widget.deleteLater()
        self.m_now_animated = False

    # Override setCurrentWidget to use our index logic
    def setCurrentWidget(self, widget):
        idx = self.indexOf(widget)
        if idx != -1:
            self.setCurrentIndex(idx)
