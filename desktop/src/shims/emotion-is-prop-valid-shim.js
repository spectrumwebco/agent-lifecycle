function isPropValid(prop) {
  if (prop.startsWith('data-') || prop.startsWith('aria-')) {
    return true;
  }
  
  const validProps = [
    'id', 'className', 'style', 'href', 'src', 'alt', 'title',
    'width', 'height', 'viewBox', 'fill', 'stroke', 'x', 'y',
    'cx', 'cy', 'r', 'd', 'transform', 'onClick', 'onMouseEnter',
    'onMouseLeave', 'onFocus', 'onBlur', 'onChange', 'value',
    'checked', 'disabled', 'placeholder', 'type', 'name', 'required',
    'initial', 'animate', 'exit', 'transition', 'variants', 'whileHover',
    'whileTap', 'whileFocus', 'whileDrag', 'drag', 'dragConstraints',
    'layout', 'layoutId', 'layoutDependency', 'onLayoutAnimationStart',
    'onLayoutAnimationComplete', 'transformTemplate', 'onDragStart',
    'onDrag', 'onDragEnd', 'dragElastic', 'dragMomentum', 'dragTransition'
  ];
  
  return validProps.includes(prop);
}

module.exports = isPropValid;
export default isPropValid;
